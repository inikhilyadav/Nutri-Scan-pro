import os
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Food Health Analyzer API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # CORS Origins (comma-separated list for local & production)
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.environ.get(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]
    
    # Specific production frontend URL (e.g. from Cloudflare Pages)
    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "")
    
    # Supabase (optional persistent storage)
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")
    
    # Port configuration (for cloud platforms like Render)
    PORT: int = int(os.environ.get("PORT", 8001))

    def get_cors_origins(self) -> List[str]:
        origins = list(self.CORS_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL.strip():
            fe = self.FRONTEND_URL.strip().rstrip("/")
            if fe not in origins:
                origins.append(fe)
        return origins

settings = Settings()
