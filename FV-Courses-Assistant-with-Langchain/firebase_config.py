from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore

def init_firebase():
    if not firebase_admin._apps:
        BASE_DIR = Path(__file__).resolve().parent
        KEY_PATH = BASE_DIR / "future_vision_firebase_key.json"
        cred = credentials.Certificate(str(KEY_PATH))
        firebase_admin.initialize_app(cred)

def get_db():
    init_firebase()
    return firestore.client()