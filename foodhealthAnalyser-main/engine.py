"""
Pure business logic: Open Food Facts lookup, health scoring, ingredient
and allergen analysis, and report assembly.

Deliberately kept free of Streamlit UI calls (it does use storage.py,
which reads st.secrets, but that works fine outside a running app — see
storage.py). Splitting this out of app.py is what lets
scripts/evaluate_accuracy.py import and exercise the real scoring logic
directly, instead of needing to boot the whole Streamlit app just to
compute a metric.
"""
import requests

import storage

NUTRIENT_FIELDS = [
    ("Sugar", "sugars_100g"),
    ("Fat", "fat_100g"),
    ("Protein", "proteins_100g"),
    ("Fiber", "fiber_100g"),
    ("Salt", "salt_100g"),
]

NOVA_LABELS = {
    1: "Unprocessed or minimally processed",
    2: "Processed culinary ingredient",
    3: "Processed food",
    4: "Ultra-processed food",
}


# ----------------------------
# Product Lookup
# ----------------------------
def get_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    headers = {
        "User-Agent": "FoodHealthAnalyzer/1.0 (Student Project; your_email@example.com)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    data = response.json()

    if data.get("status") != 1:
        return None

    return data["product"]


# ----------------------------
# Health Analysis Engine
# ----------------------------
def analyze_product(product):
    nutriments = product.get("nutriments", {})

    sugar = nutriments.get("sugars_100g", 0) or 0
    fat = nutriments.get("fat_100g", 0) or 0
    sat_fat = nutriments.get("saturated-fat_100g", 0) or 0
    salt = nutriments.get("salt_100g", 0) or 0
    sodium = nutriments.get("sodium_100g", 0) or 0
    protein = nutriments.get("proteins_100g", 0) or 0
    fiber = nutriments.get("fiber_100g", 0) or 0

    nutri_score = product.get("nutriscore_grade") or "unknown"
    nova_group = product.get("nova_group")

    score = 100
    reasons = []

    if sugar > 15:
        score -= 20
        reasons.append("High sugar content")
    elif sugar > 8:
        score -= 10
        reasons.append("Moderate sugar")

    if fat > 20:
        score -= 15
        reasons.append("High fat")

    if sat_fat > 5:
        score -= 15
        reasons.append("High saturated fat")

    if salt > 1.5:
        score -= 20
        reasons.append("High salt")

    if sodium > 0.6:
        score -= 10
        reasons.append("High sodium")

    if nova_group == 4:
        score -= 15
        reasons.append("Ultra-processed food (NOVA 4)")
    elif nova_group == 3:
        score -= 5
        reasons.append("Processed food (NOVA 3)")

    if protein >= 10:
        score += 5
        reasons.append("Good protein source")

    if fiber >= 5:
        score += 10
        reasons.append("High fiber")

    score = max(0, min(score, 100))

    if score >= 80:
        recommendation = "✅ Recommended"
    elif score >= 60:
        recommendation = "🟡 Consume in Moderation"
    else:
        recommendation = "❌ Avoid Frequent Consumption"

    return {
        "Health Score": score,
        "Recommendation": recommendation,
        "Reasons": reasons,
        "NutriScore": nutri_score.upper(),
    }


# ----------------------------
# Ingredient / Allergen / NOVA Analysis
# ----------------------------
def clean_tag(tag):
    return tag.split(":")[-1].replace("-", " ").title()


def analyze_ingredients(product):
    nova_group = product.get("nova_group")
    nova_label = NOVA_LABELS.get(nova_group, "Not classified by Open Food Facts")

    allergens_raw = product.get("allergens_tags") or []
    allergens = sorted({clean_tag(a) for a in allergens_raw})

    traces_raw = product.get("traces_tags") or []
    traces = sorted({clean_tag(t) for t in traces_raw})

    additives_raw = product.get("additives_tags") or []
    additives = sorted({clean_tag(a) for a in additives_raw})

    return {
        "NOVA Group": nova_group,
        "NOVA Label": nova_label,
        "Allergens": allergens,
        "Traces": traces,
        "Additives": additives,
    }


# ----------------------------
# Build a report dict for a barcode
#   - Tries Open Food Facts first.
#   - Falls back to the community cache (storage.py) if OFF misses.
#   - If both miss, signals the caller to offer the contribute form
#     instead of a dead end.
#   - Only includes nutrients that were actually reported — this is the
#     fix for the "some charts are blank" bug, which happened because
#     the old code defaulted every missing nutrient to 0 and charted it
#     as if that were real data.
# ----------------------------
def build_report(barcode):
    if not barcode:
        return {"error": "Enter or scan a barcode first."}

    source = "Open Food Facts"
    product = get_product(barcode)

    if product is None:
        cached = storage.cache_get(barcode)
        if cached is not None:
            product = cached
            source = "Community-added"

    if product is None:
        return {"not_found": True, "barcode": barcode}

    analysis = analyze_product(product)
    ingredient_info = analyze_ingredients(product)
    nutriments = product.get("nutriments", {})

    present_nutrients = {
        label: nutriments[key]
        for label, key in NUTRIENT_FIELDS
        if nutriments.get(key) is not None
    }

    return {
        "name": product.get("product_name", "Unknown"),
        "brand": product.get("brands", "Unknown"),
        "score": analysis["Health Score"],
        "recommendation": analysis["Recommendation"],
        "reasons": analysis["Reasons"],
        "nutriscore": analysis["NutriScore"],
        "nova_group": ingredient_info["NOVA Group"],
        "nova_label": ingredient_info["NOVA Label"],
        "allergens": ingredient_info["Allergens"],
        "traces": ingredient_info["Traces"],
        "additives": ingredient_info["Additives"],
        "image_url": product.get("image_front_url"),
        "nutrients": present_nutrients,
        "source": source,
        "barcode": barcode,
    }
