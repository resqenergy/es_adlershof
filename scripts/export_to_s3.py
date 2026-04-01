"""Script to upload datapacakges to S3."""

import sys

from dotenv import load_dotenv
from minio import Minio

from oemof_pipe.settings import (
    S3_ENDPOINT,
    S3_ACCESS_KEY,
    S3_SECRET_KEY,
    DATAPACKAGE_DIR,
)

load_dotenv()

client = Minio(
    S3_ENDPOINT,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=False,
)


def upload_datapackage(datapackage_name: str):
    dp_path = DATAPACKAGE_DIR / datapackage_name
    for local_path in dp_path.rglob("*"):
        if local_path.is_file():
            # Calculate the relative path from the datapackage root
            rel_path = local_path.relative_to(dp_path)
            # Construct the S3 key
            s3_key = f"datapackages/{datapackage_name}/{rel_path}"

            print(f"Uploading {local_path} to {s3_key}")
            client.fput_object("resq", s3_key, str(local_path))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        dp_name = sys.argv[1]
        upload_datapackage(dp_name)
    else:
        # If no argument, upload all datapackages in the directory
        for dp_path in DATAPACKAGE_DIR.iterdir():
            if dp_path.is_dir():
                print(f"Uploading datapackage: {dp_path.name}")
                upload_datapackage(dp_path.name)
