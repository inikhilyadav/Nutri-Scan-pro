"""
Computes a real, defensible accuracy number for the health-scoring /
ingredient-risk logic in engine.py — instead of a hand-picked figure
copied from somewhere else.

How to use
----------
1. Pick ~100-150 real barcodes (a mix of products you know well). For
   each one, manually decide the "correct" call by checking the actual
   label or a source you trust — not what the app currently says.
2. Fill in SAMPLE_PRODUCTS below with those barcodes + your ground
   truth.
3. Run:  python scripts/evaluate_accuracy.py
4. Paste the printed accuracy, sample size, and today's date into
   app.py's INGREDIENT_RISK_ACCURACY constant.

Re-run this periodically. Open Food Facts data changes over time, and
a stale "94% accuracy, tested Jan 2026" claim quietly rotting out of
date is worse than not showing a number at all — update the date
whenever you re-run it.
"""
from engine import analyze_product, get_product

# Each entry: a barcode, plus the ground truth you determined by hand.
# expected_recommendation should be a substring of one of:
#   "Recommended", "Consume in Moderation", "Avoid Frequent Consumption"
SAMPLE_PRODUCTS = [
    # {"barcode": "3017620422003", "expected_recommendation": "Consume in Moderation"},
    # {"barcode": "8901030826501", "expected_recommendation": "Avoid Frequent Consumption"},
]


def run():
    if not SAMPLE_PRODUCTS:
        print("SAMPLE_PRODUCTS is empty — add labeled samples first (see the docstring).")
        return

    correct = 0
    evaluated = 0

    for case in SAMPLE_PRODUCTS:
        product = get_product(case["barcode"])
        if product is None:
            print(f"  ! {case['barcode']}: not found in Open Food Facts, skipping")
            continue

        analysis = analyze_product(product)
        got = analysis["Recommendation"]
        expected = case.get("expected_recommendation")

        ok = expected is None or expected in got
        evaluated += 1
        correct += int(ok)
        print(f"  {'OK  ' if ok else 'MISS'} {case['barcode']}: got '{got}', expected '{expected}'")

    if evaluated == 0:
        print("\nNo samples could be evaluated (all lookups failed).")
        return

    print(f"\nAccuracy: {correct}/{evaluated} = {correct / evaluated:.1%}")
    print("Copy this into app.py's INGREDIENT_RISK_ACCURACY, with today's date and this sample size.")


if __name__ == "__main__":
    run()
