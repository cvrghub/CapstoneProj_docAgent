import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# VLM backend: "claude" | "internvl" | "llava"
VLM_BACKEND = os.getenv("VLM_BACKEND", "claude")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Local VLM settings (InternVL2-8B / LLaVA-7B)
LOCAL_VLM_MODEL = os.getenv("LOCAL_VLM_MODEL", "InternVL2-8B")
LOCAL_VLM_DEVICE = os.getenv("LOCAL_VLM_DEVICE", "cuda")

# Tesseract
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
OCR_DPI = int(os.getenv("OCR_DPI", "300"))

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma"))
VENDOR_COLLECTION = "vendors"

# SQLite
SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "data" / "invoices.db"))

# Validation thresholds
TOTAL_TOLERANCE = float(os.getenv("TOTAL_TOLERANCE", "0.01"))   # 1 cent
FUZZY_VENDOR_THRESHOLD = int(os.getenv("FUZZY_VENDOR_THRESHOLD", "80"))  # rapidfuzz score

# Correction
MAX_CORRECTION_ATTEMPTS = int(os.getenv("MAX_CORRECTION_ATTEMPTS", "2"))
CROP_PADDING_PX = int(os.getenv("CROP_PADDING_PX", "20"))
