import io
import logging
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from PIL import Image
import numpy as np

import engine
import barcode_utils
import storage
from core.config import settings
from schemas.models import (
    HealthCheck,
    StatsResponse,
    BarcodeValidationResponse,
    ScanImageResponse,
    ContributeRequest,
    ProductReportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Benchmark accuracy reference
INGREDIENT_RISK_ACCURACY = {
    "value": 0.94,
    "n": 150,
    "date": "2026-09-05"
}

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}


@router.get("/health", response_model=HealthCheck, tags=["Monitoring"])
def health_check():
    """
    Health check endpoint for Render, container monitoring, and load balancers.
    """
    storage_mode = "supabase" if storage.is_using_supabase() else "local"
    return HealthCheck(
        status="ok",
        model_loaded=True,
        storage_mode=storage_mode,
        version=settings.VERSION,
    )


@router.get("/api/stats", response_model=StatsResponse, tags=["Stats"])
def get_stats():
    """
    Returns total products analyzed count and accuracy statistics.
    """
    storage_mode = "supabase" if storage.is_using_supabase() else "local"
    count = storage.get_scan_count()
    return StatsResponse(
        scan_count=count,
        ingredient_risk_accuracy=INGREDIENT_RISK_ACCURACY,
        storage_mode=storage_mode,
    )


@router.get("/api/validate-barcode", response_model=BarcodeValidationResponse, tags=["Barcode"])
def validate_barcode_endpoint(barcode: str = Query(..., description="Raw or normalized barcode string")):
    """
    Cleans and normalizes a barcode string and validates the GS1 check digit.
    """
    normalized = barcode_utils.normalize_barcode(barcode)
    valid_checksum = barcode_utils.validate_checksum(normalized)
    return BarcodeValidationResponse(
        barcode=barcode,
        normalized=normalized,
        is_valid_checksum=valid_checksum,
    )


@router.get("/api/analyze/{barcode}", response_model=ProductReportResponse, tags=["Analysis"])
def analyze_barcode(barcode: str):
    """
    Fetches product information from Open Food Facts (or community cache),
    computes health score, NutriScore, NOVA category, allergens, and nutrients.
    """
    clean_code = barcode_utils.normalize_barcode(barcode)
    if not clean_code:
        raise HTTPException(status_code=400, detail="Invalid or empty barcode provided.")

    report = engine.build_report(clean_code)

    if report.get("error"):
        return ProductReportResponse(
            success=False,
            error=report["error"],
            barcode=clean_code,
        )

    if report.get("not_found"):
        return ProductReportResponse(
            success=False,
            not_found=True,
            barcode=clean_code,
        )

    # Increment scan stats on successful analysis
    try:
        storage.increment_scan_count()
    except Exception as e:
        logger.warning(f"Could not increment scan count: {e}")

    return ProductReportResponse(
        success=True,
        not_found=False,
        name=report.get("name"),
        brand=report.get("brand"),
        score=report.get("score"),
        recommendation=report.get("recommendation"),
        reasons=report.get("reasons", []),
        nutriscore=report.get("nutriscore"),
        nova_group=report.get("nova_group"),
        nova_label=report.get("nova_label"),
        allergens=report.get("allergens", []),
        traces=report.get("traces", []),
        additives=report.get("additives", []),
        image_url=report.get("image_url"),
        nutrients=report.get("nutrients", {}),
        source=report.get("source"),
        barcode=clean_code,
    )


@router.post("/api/scan/image", response_model=ScanImageResponse, tags=["Barcode"])
async def scan_image_endpoint(file: UploadFile = File(...)):
    """
    Uploads a photo containing a barcode, runs image preprocessing & pyzbar decoding,
    and returns the detected barcode and validation status.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{file.content_type}'. Please upload PNG, JPG, or WEBP.",
        )

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds maximum allowed limit (10MB).",
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        image = Image.open(io.BytesIO(contents))
        img_array = np.array(image.convert("RGB"))
    except Exception as e:
        logger.error(f"Failed to decode image: {e}")
        raise HTTPException(status_code=400, detail="Corrupted or invalid image format.")

    code, raw = barcode_utils.scan_barcode(img_array)

    if not code:
        return ScanImageResponse(
            success=False,
            message="No barcode detected. Ensure the barcode is clear, well-lit, and centered.",
        )

    checksum_ok = barcode_utils.validate_checksum(code)
    return ScanImageResponse(
        success=True,
        barcode=code,
        raw_detected=raw,
        is_valid_checksum=checksum_ok,
        message=f"Barcode detected successfully: {raw}",
    )


@router.post("/api/contribute", response_model=ProductReportResponse, tags=["Community"])
def contribute_product(req: ContributeRequest):
    """
    Saves a user-contributed product to the community cache when Open Food Facts lacks data,
    and returns its newly computed health analysis report.
    """
    barcode = barcode_utils.normalize_barcode(req.barcode)
    if not barcode:
        raise HTTPException(status_code=400, detail="Invalid barcode.")

    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Product name is required.")

    product = {
        "product_name": req.name.strip(),
        "brands": (req.brand or "Unknown").strip(),
        "nutriments": {
            "sugars_100g": req.sugar,
            "fat_100g": req.fat,
            "salt_100g": req.salt,
        },
    }

    storage.cache_set(barcode, product)
    try:
        storage.increment_scan_count()
    except Exception as e:
        logger.warning(f"Could not increment scan count: {e}")

    report = engine.build_report(barcode)
    return ProductReportResponse(
        success=True,
        not_found=False,
        name=report.get("name"),
        brand=report.get("brand"),
        score=report.get("score"),
        recommendation=report.get("recommendation"),
        reasons=report.get("reasons", []),
        nutriscore=report.get("nutriscore"),
        nova_group=report.get("nova_group"),
        nova_label=report.get("nova_label"),
        allergens=report.get("allergens", []),
        traces=report.get("traces", []),
        additives=report.get("additives", []),
        image_url=report.get("image_url"),
        nutrients=report.get("nutrients", {}),
        source=report.get("source"),
        barcode=barcode,
    )
