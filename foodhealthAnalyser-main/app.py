import numpy as np
import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt

import storage
from barcode_utils import normalize_barcode, scan_barcode, validate_checksum
from engine import build_report

st.set_page_config(page_title="Food Health Analyzer", page_icon="🥗", layout="wide")

# ----------------------------
# Set this only after running scripts/evaluate_accuracy.py against a
# real labeled sample — do not hand-pick a number here. Leave it as
# None until you have one; the UI handles that gracefully.
# Example once you have a result:
# INGREDIENT_RISK_ACCURACY = {"value": 0.94, "n": 150, "date": "2026-09-05"}
# ----------------------------
INGREDIENT_RISK_ACCURACY = None


# ----------------------------
# Light UI polish
# ----------------------------
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border-radius: 12px;
        padding: 12px 16px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------
# Render a report dict in the UI
# ----------------------------
def render_report(report):
    if "error" in report:
        st.warning(report["error"])
        return

    if report.get("not_found"):
        render_contribute_form(report["barcode"])
        return

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(report["name"])
        st.caption(report["brand"])
        if report["image_url"]:
            st.image(report["image_url"], width=180)
        st.metric("Health Score", f"{report['score']}/100")
        st.write(report["recommendation"])
        st.caption(f"NutriScore: {report['nutriscore']}")
        badge = "🟢 Verified" if report["source"] == "Open Food Facts" else "🧑‍🤝‍🧑 Community-added"
        st.caption(f"Source: {badge}")

    with col2:
        if report["nutrients"]:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            labels = list(report["nutrients"].keys())
            values = list(report["nutrients"].values())
            bars = ax.bar(labels, values, color="#2E7D32")
            ax.bar_label(bars, fmt="%.1f")
            ax.set_ylabel("grams per 100g")
            ax.set_title("Nutrition per 100g")
            ax.spines[["top", "right"]].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Nutrition breakdown isn't available for this product.")

    if report["nova_group"]:
        st.write(f"**Processing level:** NOVA {report['nova_group']} — {report['nova_label']}")
    else:
        st.write(f"**Processing level:** {report['nova_label']}")

    if report["allergens"]:
        st.error("⚠️ Allergens: " + ", ".join(report["allergens"]))
    else:
        st.success("No declared allergens")

    if report["traces"]:
        st.info("May contain traces of: " + ", ".join(report["traces"]))

    if report["additives"]:
        st.write(f"**Additives ({len(report['additives'])}):** " + ", ".join(report["additives"]))

    if report["reasons"]:
        st.write("**Notes:**")
        for r in report["reasons"]:
            st.write("- " + r)


def render_contribute_form(barcode):
    st.warning(f"No data found for barcode {barcode} — Open Food Facts doesn't have it (yet).")
    st.caption(
        "Know this product? Add the basics below and it'll be saved so the "
        "next person who scans this exact barcode gets an instant result."
    )

    with st.form(key=f"contribute_{barcode}"):
        name = st.text_input("Product name")
        brand = st.text_input("Brand")
        c1, c2, c3 = st.columns(3)
        with c1:
            sugar = st.number_input("Sugar g/100g", min_value=0.0, value=0.0, step=0.5)
        with c2:
            fat = st.number_input("Fat g/100g", min_value=0.0, value=0.0, step=0.5)
        with c3:
            salt = st.number_input("Salt g/100g", min_value=0.0, value=0.0, step=0.1)
        submitted = st.form_submit_button("Save & Analyze")

    if submitted:
        if not name:
            st.warning("Add at least a product name.")
            return
        product = {
            "product_name": name,
            "brands": brand or "Unknown",
            "nutriments": {
                "sugars_100g": sugar,
                "fat_100g": fat,
                "salt_100g": salt,
            },
        }
        storage.cache_set(barcode, product)
        st.success("Saved — thanks! Here's your analysis:")
        report = build_report(barcode)
        render_report(report)
        maybe_count_analysis(f"counted_contribute_{barcode}", barcode)


# ----------------------------
# Streamlit reruns the entire script on every interaction, so a report
# that's still on screen from a previous run would get "counted" again
# on every unrelated rerun without this guard — not just the run where
# it was actually produced.
# ----------------------------
def maybe_count_analysis(state_key: str, identifier: str):
    if st.session_state.get(state_key) != identifier:
        st.session_state[state_key] = identifier
        try:
            storage.increment_scan_count()
        except Exception:
            pass  # a stats hiccup should never break the actual report


# ----------------------------
# Shared entry flow — camera, upload, and manual search all funnel
# through this exact same function. That's deliberate: it's what
# guarantees the three paths can't silently behave differently again.
# It also shows the user precisely what barcode was detected, in an
# editable field, before ever calling the API — so a camera misread
# gets caught and fixed on the spot instead of turning into a
# confusing "not found".
# ----------------------------
def barcode_entry_flow(tab_key, initial_code=None):
    input_key = f"barcode_input_{tab_key}"
    prefill_marker = f"{tab_key}_prefill_source"

    if initial_code and st.session_state.get(prefill_marker) != initial_code:
        st.session_state[input_key] = initial_code
        st.session_state[prefill_marker] = initial_code

    typed = st.text_input(
        "Barcode number", key=input_key, placeholder="Example: 3017620422003"
    )
    code = normalize_barcode(typed)

    if code and validate_checksum(code) is False:
        st.caption(
            "⚠️ That doesn't look like a valid barcode — double-check the digits "
            "before searching. This is the most common cause of a scan saying "
            "'not found' for a product that clearly exists."
        )

    if st.button("🔎 Search & Analyze", key=f"search_{tab_key}"):
        if not code:
            st.warning("Enter or scan a barcode first.")
            return
        report = build_report(code)
        render_report(report)
        if "error" not in report and not report.get("not_found"):
            maybe_count_analysis(f"counted_{tab_key}", code)


# ----------------------------
# UI
# ----------------------------
st.title("🥗 Food Health Analyzer")
st.caption("Check your food before you eat it")

stat_col1, stat_col2 = st.columns(2)
with stat_col1:
    try:
        count = storage.get_scan_count()
        st.metric("Products analyzed", f"{count:,}+")
    except Exception:
        st.caption("Products analyzed: unavailable right now")

with stat_col2:
    if INGREDIENT_RISK_ACCURACY:
        acc = INGREDIENT_RISK_ACCURACY
        st.metric("Ingredient-risk accuracy", f"{acc['value']:.0%}")
        st.caption(f"Tested on {acc['n']} products · {acc['date']}")
    else:
        st.caption("Ingredient-risk accuracy benchmark: coming soon")

if not storage.is_using_supabase():
    st.sidebar.warning(
        "Running in local-storage mode — the counter and community cache "
        "won't survive a redeploy. Add Supabase secrets to make them "
        "permanent (see SETUP.md)."
    )

tab_camera, tab_search, tab_upload = st.tabs(
    ["📷 Scan Barcode", "🔎 Type / Search", "🖼️ Upload Image"]
)

with tab_camera:
    st.write("Point your camera at the barcode and take a photo.")
    st.caption(
        "Tip: if the preview opens your front (selfie) camera, look for a "
        "flip-camera icon and switch to the rear camera — barcodes need a "
        "close, sharp shot to scan reliably."
    )
    cam_photo = st.camera_input("Camera", key="camera_input")

    detected_code = None
    if cam_photo is not None:
        img = Image.open(cam_photo)
        code, raw = scan_barcode(np.array(img))
        if not code:
            st.warning(
                "No barcode detected. Try moving closer, improving lighting, "
                "or use the Upload Image tab instead."
            )
        else:
            st.success(f"Detected: {raw}")
            detected_code = code

    barcode_entry_flow("camera", initial_code=detected_code)

with tab_search:
    barcode_entry_flow("search")

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a photo where the barcode is clearly visible",
        type=["png", "jpg", "jpeg"],
    )

    detected_code = None
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        code, raw = scan_barcode(np.array(img))
        if not code:
            st.warning("No barcode detected in the uploaded image.")
        else:
            st.success(f"Detected: {raw}")
            detected_code = code

    barcode_entry_flow("upload", initial_code=detected_code)
