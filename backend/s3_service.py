import boto3
import uuid
import os
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME


from botocore.client import Config

def get_s3_client():
    """Create and return a boto3 S3 client."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=f"https://s3.{AWS_REGION}.amazonaws.com",
        config=Config(signature_version='s3v4')
    )


def generate_presigned_upload(filename: str, content_type: str) -> dict:
    """
    Generate a pre-signed POST request data for direct S3 upload.

    Args:
        filename: Original filename to be uploaded.
        content_type: MIME type of the file.

    Returns:
        A dict with the presigned URL, fields, and file metadata.

    Raises:
        RuntimeError: On S3 client or credentials errors.
    """
    s3 = get_s3_client()

    # Generate a unique key to avoid name collisions
    ext = os.path.splitext(filename)[1]
    unique_key = f"uploads/{uuid.uuid4().hex}{ext}"

    try:
        # Generate presigned POST data (valid for 1 hour)
        # We enforce the content type and a max size (e.g., 100MB)
        presigned_data = s3.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=unique_key,
            Fields={"Content-Type": content_type},
            Conditions=[
                {"Content-Type": content_type},
                ["content-length-range", 0, 104857600]  # Max 100 MB
            ],
            ExpiresIn=3600
        )

        return {
            "presigned_data": presigned_data,
            "s3_key": unique_key,
            "original_filename": filename,
            "bucket": S3_BUCKET_NAME,
            "region": AWS_REGION,
        }

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found or invalid.")
    except ClientError as e:
        raise RuntimeError(f"S3 presigned URL generation failed: {e.response['Error']['Message']}")


def list_s3_files() -> list[dict]:
    """
    List all files in the uploads/ prefix of the S3 bucket.

    Returns:
        A list of dicts with key, size, and last_modified fields.
    """
    s3 = get_s3_client()
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix="uploads/")
        objects = response.get("Contents", [])
        return [
            {
                "s3_key": obj["Key"],
                "filename": obj["Key"].split("/", 1)[-1],
                "size_bytes": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            }
            for obj in objects
            if obj["Key"] != "uploads/"  # exclude the prefix folder entry
        ]
    except ClientError as e:
        raise RuntimeError(f"Failed to list S3 objects: {e.response['Error']['Message']}")


def delete_s3_file(s3_key: str) -> bool:
    """
    Delete a file from the S3 bucket by its key.

    Args:
        s3_key: The full S3 object key.

    Returns:
        True on success.

    Raises:
        RuntimeError: On S3 client errors.
    """
    s3 = get_s3_client()
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return True
    except ClientError as e:
        raise RuntimeError(f"Failed to delete S3 object: {e.response['Error']['Message']}")
