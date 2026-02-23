"""
Drishyamitra - Configuration
Centralized configuration for the AI-Powered Photo Management System.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# PATH CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ORGANIZED_FOLDER = os.path.join(BASE_DIR, "organized")
DB_PATH = os.path.join(BASE_DIR, "drishyamitra.db")
STORAGE_FILE = os.path.join(BASE_DIR, "face_data.json")

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ORGANIZED_FOLDER, exist_ok=True)

# -----------------------------
# DATABASE
# -----------------------------
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

# -----------------------------
# DEEPFACE CONFIG
# -----------------------------
FACE_DETECTION_BACKEND = "retinaface"       # retinaface, mtcnn, opencv
FACE_RECOGNITION_MODEL = "Facenet512"       # Facenet512, VGG-Face, ArcFace
FACE_SIMILARITY_THRESHOLD = 0.68           # Cosine similarity threshold for face matching
FACE_DISTANCE_METRIC = "cosine"

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

# -----------------------------
# GROQ (Chatbot LLM)
# -----------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"  # or "mixtral-8x7b-32768"

# -----------------------------
# GOOGLE GEMINI (Fallback / Naming)
# -----------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# -----------------------------
# GMAIL API
# -----------------------------
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")

# -----------------------------
# WHATSAPP
# -----------------------------
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")

# -----------------------------
# APP CONFIG
# -----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "drishyamitra-secret-key-change-in-prod")
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
HOST = "0.0.0.0"
PORT = 5001
