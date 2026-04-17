<<<<<<< HEAD
# Secure-cloud
=======
# ☁️ Secure Cloud File Storage System

A full-stack web application for uploading and managing files privately on **AWS S3**, built with **FastAPI** (backend) and vanilla **HTML / CSS / JavaScript** (frontend).

---

## 📁 Project Structure

```
secure_cloud/
├── backend/
│   ├── main.py            # FastAPI app — all routes
│   ├── s3_service.py      # boto3 S3 logic (upload, list, delete)
│   ├── config.py          # Load & validate environment variables
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Template for environment variables
│
└── frontend/
    ├── index.html         # Single-page UI
    ├── style.css          # Dark-mode premium design
    └── app.js             # Fetch API, drag-and-drop, file list
```

---

## ⚙️ Backend Setup

### 1. Create a virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure AWS credentials

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-private-bucket-name
```

> ⚠️ **Never commit `.env` to version control.**
> Add it to `.gitignore` immediately.

### 4. Ensure your S3 bucket is private

In the AWS Console:
- Block all public access (default for new buckets ✅)
- No bucket policy granting public read

### 5. Run the FastAPI server

```bash
uvicorn main:app --reload
```

Server will start at: **http://127.0.0.1:8000**

Interactive API docs: **http://127.0.0.1:8000/docs**

---

## 🌐 Frontend Setup

No build step needed — open `frontend/index.html` directly in your browser:

```bash
# Option A — double-click index.html in Explorer

# Option B — serve with Python
cd frontend
python -m http.server 5500
# then open http://localhost:5500
```

> Make sure the FastAPI server is running before you use the frontend.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload a file to S3 |
| `GET` | `/files` | List all files in S3 |
| `DELETE` | `/files/{s3_key}` | Delete a file from S3 |

### Example — Upload via cURL

```bash
curl -X POST http://127.0.0.1:8000/upload \
  -F "file=@/path/to/your/file.pdf"
```

### Example — Success Response

```json
{
  "success": true,
  "message": "'report.pdf' uploaded successfully.",
  "data": {
    "s3_key": "uploads/a3f9c12d.pdf",
    "original_filename": "report.pdf",
    "size_bytes": 204800,
    "bucket": "your-private-bucket",
    "region": "us-east-1"
  }
}
```

---

## 🛡️ Security Notes

- Files are stored in a **private S3 bucket** — no public URLs are generated.
- AWS credentials are loaded from environment variables, never hardcoded.
- CORS is open (`*`) for local development. Restrict it in production.

---

## 🚀 Next Steps (not included yet)

- User authentication (JWT / OAuth)
- Pre-signed URLs for secure temporary downloads
- File type / size validation
- Database for file metadata
- Progress bar using real XHR upload events
>>>>>>> 6bcd408 (Initial commit)
