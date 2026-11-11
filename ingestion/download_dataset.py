#!/usr/bin/env python3
"""
SchemeSathi - Dataset Downloader
Downloads the official Hugging Face dataset:
smartduketech/indian-government-schemes-2025
and saves it locally as a raw parquet file without modifying original data.
"""

import os
import sys
from pathlib import Path
from loguru import logger
import pandas as pd

# Path configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RAW_FILE_PATH = RAW_DATA_DIR / "schemes_raw.parquet"
DATASET_NAME = "smartduketech/indian-government-schemes-2025"

def download_dataset(force: bool = False) -> pd.DataFrame:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if RAW_FILE_PATH.exists() and not force:
        logger.info(f"Raw dataset already exists at {RAW_FILE_PATH}. Loading cached file.")
        df = pd.read_parquet(RAW_FILE_PATH)
        print_dataset_summary(df)
        return df

    logger.info(f"Downloading dataset '{DATASET_NAME}' from Hugging Face...")
    
    df = None
    # Method 1: HuggingFace datasets library
    try:
        from datasets import load_dataset
        ds = load_dataset(DATASET_NAME, split="train")
        df = ds.to_pandas()
        logger.info("Successfully downloaded via datasets library.")
    except Exception as e1:
        logger.warning(f"Method 1 failed ({e1}). Trying direct parquet download via huggingface_hub...")
        try:
            from huggingface_hub import hf_hub_download
            file_path = hf_hub_download(
                repo_id=DATASET_NAME,
                filename="data/train-00000-of-00001.parquet",
                repo_type="dataset"
            )
            df = pd.read_parquet(file_path)
            logger.info("Successfully downloaded via huggingface_hub.")
        except Exception as e2:
            logger.warning(f"Method 2 failed ({e2}). Trying pandas direct read from HF parquet URL...")
            try:
                # Direct url fallback
                hf_url = f"https://huggingface.co/datasets/{DATASET_NAME}/resolve/main/data/train-00000-of-00001.parquet"
                df = pd.read_parquet(hf_url)
                logger.info("Successfully downloaded via direct URL.")
            except Exception as e3:
                logger.error(f"Failed to download dataset: {e3}")
                raise RuntimeError(f"Could not download {DATASET_NAME}: {e3}")

    # Preserve the raw parquet file untouched
    df.to_parquet(RAW_FILE_PATH, index=False)
    logger.success(f"Preserved raw dataset at {RAW_FILE_PATH} ({len(df)} records, size: {RAW_FILE_PATH.stat().st_size / 1024:.1f} KB)")
    
    print_dataset_summary(df)
    return df

def print_dataset_summary(df: pd.DataFrame):
    print("\n" + "=" * 60)
    print(" Indian Government Schemes 2025 - Dataset Inspection")
    print("=" * 60)
    print(f"Total Records     : {len(df)}")
    print(f"Total Columns     : {len(df.columns)}")
    print(f"Columns Available : {list(df.columns)}")
    print(f"License           : CC BY 4.0 (myscheme.gov.in provenance)")
    
    if "state" in df.columns:
        print("\nState Distribution (Top 10):")
        print(df["state"].value_counts().head(10))
    
    if "category" in df.columns:
        print("\nTop Categories:")
        print(df["category"].value_counts().head(10))
        
    null_counts = df.isnull().sum()
    print("\nMissing Values Sample:")
    for col in ["eligibility_income_max", "apply_url", "official_url", "documents_required", "eligibility_text"]:
        if col in df.columns:
            print(f"  - {col}: {null_counts[col]} nulls ({null_counts[col] / len(df) * 100:.1f}%)")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    force_download = "--force" in sys.argv
    download_dataset(force=force_download)

