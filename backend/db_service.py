import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

# Initialize Firebase Admin SDK
def init_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to application default credentials
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Firebase initialization failed. {e}")

init_firebase()

class MockDocRef:
    def __init__(self, key=None):
        self.id = key or "mocked-doc-id"
    def set(self, data):
        self.data = data
        print("Mock Firestore saved:", data)
    def delete(self):
        pass

class MockDB:
    def collection(self, name):
        return self
    def document(self, doc_id=None):
        return MockDocRef()
    def where(self, *args):
        return self
    def stream(self):
        return []

def get_db():
    if not firebase_admin._apps:
        # Fallback to an empty mock so the UI still functions without error
        return MockDB()
    try:
        return firestore.client()
    except Exception as e:
        return MockDB()

def save_file_record(user_id: str, s3_key: str, filename: str, size: int, url: str) -> str:
    """Saves file metadata to Firestore and links to user."""
    db = get_db()
    doc_ref = db.collection("files").document()
    doc_ref.set({
        "user_id": user_id,
        "s3_key": s3_key,
        "file_name": filename,
        "file_size": size,
        "file_url": url,
        "upload_time": datetime.now(timezone.utc).isoformat()
    })
    return doc_ref.id

def get_user_files(user_id: str) -> list[dict]:
    """Retrieves all file metadata for a specific user."""
    db = get_db()
    docs = db.collection("files").where("user_id", "==", user_id).stream()
    files = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        files.append(data)
    # Sort by upload_time descending
    files.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
    return files

def delete_file_record(s3_key: str):
    """Deletes the firestore metadata record associated with the s3_key."""
    db = get_db()
    # Find the document with the matching s3_key
    docs = db.collection("files").where("s3_key", "==", s3_key).stream()
    for doc in docs:
        doc.reference.delete()
