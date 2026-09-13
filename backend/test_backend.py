import sys
from pathlib import Path
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app
import io
from PIL import Image, ImageDraw

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    data = res.json()
    assert data["status"] in ("ok", "healthy")
    assert data["model_loaded"] is True
    print("[PASS] Health check passed:", data)

def test_stats():
    res = client.get("/api/stats")
    assert res.status_code == 200, f"Stats failed: {res.text}"
    data = res.json()
    assert "scan_count" in data
    assert "storage_mode" in data
    print("[PASS] Stats endpoint passed:", data)

def test_validate_barcode():
    # Valid barcode with correct check digit (Nutella: 3017620422003)
    res = client.get("/api/validate-barcode?barcode=3017620422003")
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid_checksum"] is True
    assert data["normalized"] == "3017620422003"
    
    # 12-digit UPC-A should be padded
    res2 = client.get("/api/validate-barcode?barcode=012345678905")
    assert res2.status_code == 200
    assert len(res2.json()["normalized"]) == 13
    print("[PASS] Barcode validation passed")

def test_analyze_nutella():
    res = client.get("/api/analyze/3017620422003")
    assert res.status_code == 200, f"Analyze failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "score" in data
    assert data["score"] is not None
    assert "nutrients" in data
    print("[PASS] Nutella analysis passed: Score", data["score"], data["recommendation"])

def test_contribute_flow():
    test_barcode = "0000000000001"
    payload = {
        "barcode": test_barcode,
        "name": "Organic Oat Flakes",
        "brand": "Pure Oats",
        "sugar": 1.2,
        "fat": 6.8,
        "salt": 0.02
    }
    res = client.post("/api/contribute", json=payload)
    assert res.status_code == 200, f"Contribute failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert data["name"] == "Organic Oat Flakes"
    assert data["source"] == "Community-added"
    assert data["score"] >= 80
    print("[PASS] Contribution flow passed: Score", data["score"], data["source"])

def test_scan_image_validation():
    # Create a small blank image in memory
    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    res = client.post(
        "/api/scan/image",
        files={"file": ("test.png", buf, "image/png")}
    )
    assert res.status_code == 200
    data = res.json()
    # Blank image should report success=False, no barcode detected
    assert data["success"] is False
    assert "No barcode detected" in data["message"]
    print("[PASS] Scan image validation passed:", data["message"])

if __name__ == "__main__":
    test_health()
    test_stats()
    test_validate_barcode()
    test_analyze_nutella()
    test_contribute_flow()
    test_scan_image_validation()
    print("\nAll backend integration tests passed successfully!")
