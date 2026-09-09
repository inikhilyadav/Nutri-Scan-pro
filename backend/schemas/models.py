from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class HealthCheck(BaseModel):
    status: str = "ok"
    model_loaded: bool = True
    storage_mode: str = "local"
    version: str = "1.0.0"

class StatsResponse(BaseModel):
    scan_count: int
    ingredient_risk_accuracy: Optional[Dict[str, Any]] = None
    storage_mode: str

class BarcodeValidationResponse(BaseModel):
    barcode: str
    normalized: str
    is_valid_checksum: Optional[bool] = None

class ScanImageResponse(BaseModel):
    success: bool
    barcode: Optional[str] = None
    raw_detected: Optional[str] = None
    is_valid_checksum: Optional[bool] = None
    message: str

class ContributeRequest(BaseModel):
    barcode: str = Field(..., min_length=1, description="Barcode of the product")
    name: str = Field(..., min_length=1, description="Product name")
    brand: Optional[str] = "Unknown"
    sugar: float = Field(0.0, ge=0.0, description="Sugar in g per 100g")
    fat: float = Field(0.0, ge=0.0, description="Fat in g per 100g")
    salt: float = Field(0.0, ge=0.0, description="Salt in g per 100g")

class ProductReportResponse(BaseModel):
    success: bool = True
    not_found: bool = False
    error: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    score: Optional[int] = None
    recommendation: Optional[str] = None
    reasons: Optional[List[str]] = None
    nutriscore: Optional[str] = None
    nova_group: Optional[int] = None
    nova_label: Optional[str] = None
    allergens: Optional[List[str]] = None
    traces: Optional[List[str]] = None
    additives: Optional[List[str]] = None
    image_url: Optional[str] = None
    nutrients: Optional[Dict[str, float]] = None
    source: Optional[str] = None
    barcode: Optional[str] = None
