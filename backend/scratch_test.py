import sys
import boto3
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET_NAME
from botocore.client import Config

def test():
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        config=Config(signature_version="s3v4")
    )
    res = s3.generate_presigned_post(
        Bucket=S3_BUCKET_NAME,
        Key="test.txt",
        Fields={"Content-Type": "text/plain"},
        Conditions=[{"Content-Type": "text/plain"}],
        ExpiresIn=3600
    )
    print("URL:", res['url'])

if __name__ == "__main__":
    test()
