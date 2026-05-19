"""Module for reading files from S3 or local folders."""

from __future__ import annotations

from io import BytesIO
import json
import yaml

import pandas as pd
from pathlib import Path
from minio import Minio

from settings import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, STORE_FILES_LOCALLY

S3_BUCKET = "resq"
S3_FOLDER = "resq_demands"

STORAGE_OPTIONS = {
    "key": S3_ACCESS_KEY,
    "secret": S3_SECRET_KEY,
    "endpoint_url": f"http://{S3_ENDPOINT}",
}


def read_file(filepath: str | Path, **kwargs) -> pd.DataFrame | dict:
    """Try to read file from S3 or local path if S3 connection is not set up."""

    def get_data() -> dict:
        payload = response.read().decode("utf-8")
        if filepath_rel.suffix == ".json":
            return json.loads(payload)
        elif filepath_rel.suffix == ".yaml":
            return yaml.safe_load(payload)
        else:
            raise TypeError(
                f"Cannot read file with type '{filepath_rel.suffix}' from S3."
            )

    filepath = Path(filepath).absolute()

    if S3_ENDPOINT is None:
        if filepath.suffix == ".csv":
            return pd.read_csv(filepath, **kwargs)
        elif filepath.suffix == ".json":
            return json.load(open(filepath, encoding="utf-8"))
        elif filepath.suffix == ".yaml":
            return yaml.safe_load(open(filepath, encoding="utf-8"))

    # Get file from S3
    filepath_rel = filepath.relative_to(Path.cwd())

    if filepath_rel.suffix == ".csv":
        filepath_s3 = f"s3://{S3_BUCKET}/{S3_FOLDER}/{filepath_rel}"
        return pd.read_csv(filepath_s3, storage_options=STORAGE_OPTIONS, **kwargs)
    elif filepath_rel.suffix == ".xlsx":
        filepath_s3 = f"s3://{S3_BUCKET}/{S3_FOLDER}/{filepath_rel}"
        return pd.read_excel(filepath_s3, storage_options=STORAGE_OPTIONS, **kwargs)
    elif filepath_rel.suffix in (".json", ".yaml"):
        filepath_s3 = f"{S3_FOLDER}/{filepath_rel}"
        client = Minio(
            S3_ENDPOINT,
            access_key=S3_ACCESS_KEY,
            secret_key=S3_SECRET_KEY,
            secure=False,
        )
        response = client.get_object(S3_BUCKET, filepath_s3)
        return get_data()


def write_file(data: pd.DataFrame | dict, filepath: str | Path, **kwargs) -> None:
    """Try to write file to S3 or local path if S3 connection is not set up."""

    def get_payload():
        if filepath_rel.suffix == ".json":
            return json.dumps(data, **kwargs).encode("utf-8")
        elif filepath_rel.suffix == ".yaml":
            return yaml.safe_dump(data, **kwargs).encode("utf-8")
        else:
            raise TypeError(
                f"Cannot store files with type '{filepath_rel.suffix}' on S3."
            )

    filepath = Path(filepath).absolute()

    if S3_ENDPOINT is None or STORE_FILES_LOCALLY:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (pd.DataFrame, pd.Series)):
            data.to_csv(filepath, **kwargs)
        elif filepath.suffix == ".json":
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, **kwargs)
        elif filepath.suffix == ".yaml":
            with filepath.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, **kwargs)

    if S3_ENDPOINT is None:
        return

    # Write file to S3
    filepath_rel = filepath.relative_to(Path.cwd())

    if isinstance(data, (pd.DataFrame, pd.Series)):
        filepath_s3 = f"s3://{S3_BUCKET}/{S3_FOLDER}/{filepath_rel}"
        data.to_csv(filepath_s3, storage_options=STORAGE_OPTIONS, **kwargs)
        return

    payload = get_payload()
    stream = BytesIO(payload)
    filepath_s3 = f"{S3_FOLDER}/{filepath_rel}"
    client = Minio(
        S3_ENDPOINT,
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        secure=False,
    )
    client.put_object(S3_BUCKET, filepath_s3, stream, len(payload))
