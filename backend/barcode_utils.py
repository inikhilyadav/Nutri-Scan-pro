"""
Barcode utilities: cleaning, checksum validation, and image preprocessing.
"""
import re
import cv2
import numpy as np

try:
    from pyzbar.pyzbar import decode as zbar_decode
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False


def clean_barcode(raw: str) -> str:
    """Strip everything except digits."""
    return re.sub(r"\D", "", raw or "")


def normalize_barcode(raw: str) -> str:
    """
    Normalize a scanned/typed barcode to the form Open Food Facts expects.
    UPC-A (12 digits) is zero-padded to a 13-digit EAN.
    """
    code = clean_barcode(raw)
    if len(code) == 12:
        code = "0" + code
    return code


def validate_checksum(code: str):
    """
    Validate the GS1 check digit for a 13-digit EAN (or zero-padded UPC-A).
    Returns True/False, or None if the length isn't one we validate.
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
    """
    if image_array is None or not PYZBAR_AVAILABLE:
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
