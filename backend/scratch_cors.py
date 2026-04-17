import sys
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME

def configure_cors():
    print(f"Applying CORS to bucket '{S3_BUCKET_NAME}' in region '{AWS_REGION}'...")
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': []
        }]
    }
    try:
        s3.put_bucket_cors(Bucket=S3_BUCKET_NAME, CORSConfiguration=cors_configuration)
        print("CORS successfully applied! ✅")
    except Exception as e:
        print(f"Failed to apply CORS: {e}")

if __name__ == "__main__":
    configure_cors()
