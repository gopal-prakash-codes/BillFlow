import io
import time
import os
import zipfile
from datetime import datetime
from typing import List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from loguru import logger as log

from app.config import config as global_config

from .config import config

s3_client = boto3.client(
    "s3",
    aws_access_key_id=global_config.aws_access_key,
    aws_secret_access_key=global_config.aws_secret_key,
    region_name=global_config.aws_region_name,
)


def get_object_path(image_name: str, extension: str):
    return f"{image_name}.{extension}"


def upload_file(file_name, file_data, bucket, object_name, user_id, invoice_id, attachment_type):
    # Upload the file
    try:
        s3_client.upload_fileobj(io.BytesIO(file_data), bucket, object_name, ExtraArgs={
            "Metadata": {
                "date_created": str(datetime.now().date()),
                "user_id": user_id,
                "invoice_id": invoice_id,
                "type": attachment_type
            }
        })
        pass
    except ClientError as e:
        log.error(e)
        return False
    return True


def upload_bytes_to_s3(object: bytes, filename: str, extension: str) -> str:
    start = time.time()
    s3_client.upload_fileobj(
        io.BytesIO(object), config.s3_bucket_name, f"{filename}.{extension}"
    )
    log.debug(
        f"Uploaded {filename}.{extension} to s3 in {round(time.time() - start, ndigits=2)}"
    )
    return get_object_path(filename, extension)


def upload_string_to_s3(object: str, filename: str, extension: str) -> str:
    start = time.time()
    s3_client.put_object(
        Bucket=config.s3_bucket_name, Body=object, Key=f"{filename}.{extension}"
    )
    log.debug(
        f"Uploaded {filename}.{extension} to s3 in {round(time.time() - start, ndigits=2)}"
    )
    return get_object_path(filename, extension)


def download_file(bucket, object_name, local_file_path):
    try:
        s3_client.download_file(bucket, object_name, local_file_path)
    except NoCredentialsError:
        return False
    return True


def get_attachments_from_s3(invoice_id: str) -> List[str]:
    # List objects in the S3 bucket
    response = s3_client.list_objects(Bucket='apiattach')

    # Extract keys from the response for the given invoice_id
    attachments = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].startswith(invoice_id)]

    return attachments


def create_zip_buffer(attachments: List[str]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for attachment_key in attachments:
            attachment_data = s3_client.get_object(Bucket='apiattach', Key=attachment_key)['Body'].read()
            zip_file.writestr(os.path.basename(attachment_key), attachment_data)
    zip_buffer.seek(0)
    return zip_buffer
