"""
Barcode utilities: cleaning, checksum validation, and image preprocessing.

Why this file exists
---------------------
The original app called pyzbar directly on whatever frame came out of
st.camera_input or a photo upload, and sent whatever string it got
straight to Open Food Facts. That's how you end up with the bug where a
live camera scan says "not found" but retyping the same-looking number
(or uploading a clearer photo) works: pyzbar can and does misread a
digit on a blurry / low-res / poorly lit frame, and a misread code will
genuinely have no match in Open Food Facts — the app isn't wrong, the
input it was given was wrong. Camera phones/webcams also commonly open
the front-facing camera by default in mobile browsers, which makes this
worse since it's the wrong camera for a close-up shot in the first
place.

This module fixes what's fixable in code:
  - normalize_barcode(): every entry path (camera / upload / typed) is
    funneled through the same cleanup, so they can't silently diverge.
  - validate_checksum(): catches a misread *before* it becomes a
    confusing "not found" — a barcode with a bad check digit is almost
    certainly a misread, not a real product.
  - scan_barcode(): tries a couple of lightweight preprocessing passes
    (grayscale, upscaling small frames, contrast boost) since pyzbar's
    hit rate on raw phone/webcam frames is noticeably worse than on a
    cleaned-up version of the same photo.
"""
import re

import cv2
import numpy as np
from pyzbar.pyzbar import decode as zbar_decode


def clean_barcode(raw: str) -> str:
    """Strip everything except digits."""
    return re.sub(r"\D", "", raw or "")


def normalize_barcode(raw: str) -> str:
    """
    Normalize a scanned/typed barcode to the form Open Food Facts expects.

    UPC-A (12 digits) is zero-padded to a 13-digit EAN so a code that
    came from a camera scan and the "same" code retyped by hand always
    resolve identically — this was the other half of the "scan says not
    found, manual entry works" bug when it wasn't a straight misread.
    """
    code = clean_barcode(raw)
    if len(code) == 12:
        code = "0" + code
    return code


def validate_checksum(code: str):
    """
    Validate the GS1 check digit for a 13-digit EAN. This also covers
    UPC-A once normalize_barcode() has zero-padded it to 13 digits,
    since UPC-A and EAN-13 use the same checksum algorithm.

    Returns True/False, or None if the length isn't one we validate
    (e.g. EAN-8, or something non-standard) — those aren't blocked,
    just not checked.
    """
    if len(code) != 13 or not code.isdigit():
        return None

    digits = [int(c) for c in code]
    total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits[:12]))
    check_digit = (10 - (total % 10)) % 10
    return check_digit == digits[12]


def _candidate_frames(gray):
    """Yield a few preprocessed versions of a grayscale frame to try."""
    yield gray

    h, w = gray.shape[:2]
    if max(h, w) < 900:
        scale = 900 / max(h, w)
        yield cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    yield cv2.equalizeHist(gray)


def scan_barcode(image_array):
    """
    Detect a barcode from an RGB (or grayscale) numpy image.

    Returns (normalized_code, raw_detected_code) or (None, None).
    raw_detected_code is what pyzbar actually read, before normalization
    — useful to show the user exactly what was detected.
    """
    if image_array is None:
        return None, None

    img = np.asarray(image_array)

    if img.ndim == 2:
        gray = img
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    for frame in _candidate_frames(gray):
        detected = zbar_decode(frame)
        if detected:
            raw = detected[0].data.decode("utf-8").strip()
            return normalize_barcode(raw), raw

    return None, None
