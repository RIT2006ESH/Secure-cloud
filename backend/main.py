from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config import validate_config
from s3_service import generate_presigned_upload, list_s3_files, delete_s3_file

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class ConfirmUploadRequest(BaseModel):
    user_id: str
    s3_key: str
    filename: str
    size_bytes: int
    url: str

# Validate AWS config on startup
validate_config()

app = FastAPI(
    title="Secure Cloud File Storage API",
    description="FastAPI backend for uploading and managing files on AWS S3.",
    version="1.0.0",
)

# Allow requests from the frontend (served on any origin during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Secure Cloud File Storage API is running."}


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@app.post("/presigned-url", tags=["Files"])
async def get_presigned_url(request: PresignedUrlRequest):
    """
    Generate a pre-signed URL to upload a file directly to the private AWS S3 bucket.

    - Returns the S3 presigned URL, required form fields, and file metadata.
    """
    if not request.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    try:
        result = generate_presigned_upload(request.filename, request.content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": f"Presigned URL generated for '{request.filename}'.",
            "data": result,
        },
    )


# ---------------------------------------------------------------------------
# Confirm Upload
# ---------------------------------------------------------------------------

@app.post("/confirm-upload", tags=["Files"])
def confirm_upload(request: ConfirmUploadRequest):
    """
    Confirm file upload to S3 and save metadata to Firestore.
    """
    from db_service import save_file_record
    try:
        doc_id = save_file_record(
            user_id=request.user_id,
            s3_key=request.s3_key,
            filename=request.filename,
            size=request.size_bytes,
            url=request.url
        )
        return {"success": True, "message": "Metadata saved.", "file_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# List files
# ---------------------------------------------------------------------------

@app.get("/files", tags=["Files"])
def list_files(user_id: str = "test_user"):
    """
    List all files for a specific user from Firestore.
    """
    from db_service import get_user_files
    try:
        files = get_user_files(user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
        
    formatted_files = []
    for f in files:
        formatted_files.append({
            "id": f.get("id"),
            "s3_key": f.get("s3_key"),
            "filename": f.get("file_name"),
            "size_bytes": f.get("file_size"),
            "last_modified": f.get("upload_time"),
            "url": f.get("file_url")
        })

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "total": len(formatted_files),
            "files": formatted_files,
        },
    )


# ---------------------------------------------------------------------------
# Delete file
# ---------------------------------------------------------------------------

@app.delete("/files/{s3_key:path}", tags=["Files"])
def delete_file(s3_key: str):
    """
    Delete a file from S3 by its key and remove its Firestore metadata.
    """
    from db_service import delete_file_record
    try:
        delete_s3_file(s3_key)
        delete_file_record(s3_key)
    except Exception as exc:
        # Continue to delete DB record even if S3 fails
        delete_file_record(s3_key)
        raise HTTPException(status_code=500, detail=str(exc))

    return JSONResponse(
        status_code=200,
        content={"success": True, "message": f"File '{s3_key}' deleted successfully."},
    )
