# Food Health Analyzer

Scan a barcode (camera, uploaded photo, or typed manually) and get a health
score, NutriScore, NOVA processing level, allergens, additives, and a
nutrient chart, pulled from the Open Food Facts API.

Pure Streamlit — link to follow:"https://foodhealthanalyzer.streamlit.app/"
[https://foodhealthanalyzer.streamlit.app/]

## Setup (VS Code)

1. Open this folder in VS Code: `File > Open Folder`
2. Open a terminal: `` Ctrl+` `` (Windows/Linux) or `` Cmd+` `` (Mac)
3. Create and activate a virtual environment:

   **Windows**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

   **Mac / Linux**
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. **Linux only** — install the barcode-decoding system library (Windows/Mac
   get this bundled automatically with the `pyzbar` pip package):
   ```
   sudo apt-get install libzbar0
   ```

6. Run it:
   ```
   streamlit run app.py
   ```

   It opens automatically at `http://localhost:8501` in your browser.

For the one-time Supabase setup that makes the live counter and
community cache permanent (recommended before sharing the link widely),
see [SETUP.md](SETUP.md). The app works without it — it just falls back
to a local file that won't survive a redeploy.

## Project structure

```
food-health-analyzer/
├── app.py                          # UI only — tabs, rendering, wiring
├── engine.py                       # pure logic: OFF lookup, scoring, report building
├── barcode_utils.py                # barcode normalization, checksum check, image preprocessing
├── storage.py                      # Supabase-backed counter + community cache (local fallback)
├── scripts/
│   ├── evaluate_accuracy.py        # computes a real accuracy figure — see SETUP.md step 4
│   └── wake_streamlit.py           # used by the keep-alive GitHub Action
├── .github/workflows/keepalive.yml # scheduled job: wakes the app, pings Supabase
├── .streamlit/config.toml          # theme
├── requirements.txt
├── SETUP.md
└── README.md
```

## How it works

- `engine.get_product()` — looks up a barcode via the Open Food Facts API
- `engine.analyze_product()` — scores the product 0-100 based on sugar, fat,
  salt, sodium, NOVA processing level, protein, and fiber
- `engine.analyze_ingredients()` — pulls NOVA group, allergens, traces, and
  additives
- `engine.build_report()` — tries Open Food Facts first, then the community
  cache (`storage.py`) if that misses; only includes nutrients that were
  actually reported, rather than defaulting missing ones to 0
- `barcode_utils.scan_barcode()` — decodes a barcode out of a photo (camera
  or upload), trying a couple of preprocessing passes (grayscale, upscale,
  contrast) since raw phone/webcam frames don't always decode cleanly on
  the first attempt
- `barcode_utils.validate_checksum()` — flags a barcode whose check digit
  doesn't add up, which is almost always a misread rather than a real
  product — this is shown to the user *before* the search fires
- All three input tabs (camera / type / upload) funnel through the same
  `barcode_entry_flow()` in `app.py`, so they can't silently behave
  differently from each other

## Notes

- No API key required for Open Food Facts.
- If a barcode still isn't found after the checksum passes, the app offers
  a quick form to add the product manually — it gets saved to the shared
  cache so the next person who scans that exact barcode gets an instant
  hit instead of another "not found".
