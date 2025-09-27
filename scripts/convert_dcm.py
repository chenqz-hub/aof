"""
Convert DICOM directories under data/raw/ to de-identified NIfTI files in data/processed/.

Features:
- Walk `data/raw/` for DICOM series (assumes one series per subfolder).
- Read DICOM headers with pydicom, remove common patient-identifying tags.
- Save anonymized DICOMs (optional) and write a mapping Excel at data/processed/mapping.xlsx.
- If `dcm2niix` is available on PATH, call it to create nii.gz; otherwise save a minimal NIfTI using nibabel (stacked slices).

Usage:
    python scripts/convert_dcm.py

This script is intentionally conservative. Review `docs/data-handling.md` before running on PHI.
"""

import os
import sys
import logging
from pathlib import Path
import subprocess
from typing import List

import pydicom
import numpy as np
import nibabel as nib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("convert_dcm")

ANON_TAGS = [
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0010, 0x0032),  # PatientBirthTime
    (0x0008, 0x0090),  # ReferringPhysicianName
]


def find_series(raw_root: Path) -> List[Path]:
    """Find series folders under raw_root. Assumes each immediate subdirectory is a series."""
    if not raw_root.exists():
        logger.error("Raw data directory does not exist: %s", raw_root)
        return []
    series = [p for p in raw_root.iterdir() if p.is_dir()]
    logger.info("Found %d series folders", len(series))
    return series


def anonymize_dataset(ds: pydicom.dataset.FileDataset) -> pydicom.dataset.FileDataset:
    for tag in ANON_TAGS:
        if tag in ds:
            del ds[tag]
    # Optionally overwrite StudyDate with blank or shifted value
    if (0x0008, 0x0020) in ds:
        ds[(0x0008, 0x0020)].value = ""
    return ds


def load_slices(series_folder: Path) -> List[pydicom.dataset.FileDataset]:
    files = sorted([f for f in series_folder.iterdir() if f.is_file()])
    slices = []
    for f in files:
        try:
            ds = pydicom.dcmread(str(f))
            slices.append(ds)
        except Exception as e:
            logger.warning("Skipping file %s: %s", f, e)
    return slices


def write_anonymized_dicoms(slices: List[pydicom.dataset.FileDataset], out_folder: Path):
    out_folder.mkdir(parents=True, exist_ok=True)
    for i, ds in enumerate(slices):
        anon = anonymize_dataset(ds)
        out_path = out_folder / f"IM_{i:04d}.dcm"
        anon.save_as(str(out_path))


def try_dcm2niix(series_folder: Path, out_folder: Path) -> bool:
    """Attempt to run dcm2niix. Returns True if successful and output was created."""
    try:
        cmd = ["dcm2niix", "-z", "y", "-o", str(out_folder), str(series_folder)]
        logger.info("Running: %s", " ".join(cmd))
        res = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("dcm2niix output: %s", res.stdout.strip())
            return True
        else:
            logger.warning("dcm2niix failed: %s", res.stderr.strip())
            return False
    except FileNotFoundError:
        logger.info("dcm2niix not found on PATH")
        return False


def make_nifti_from_slices(slices: List[pydicom.dataset.FileDataset], out_path: Path):
    # Basic stacking of PixelData assuming same Rows/Columns and consistent orientation
    imgs = []
    for ds in slices:
        arr = ds.pixel_array
        imgs.append(arr)
    vol = np.stack(imgs, axis=-1)
    affine = np.eye(4)
    nif = nib.Nifti1Image(vol.astype(np.int16), affine)
    nib.save(nif, str(out_path))


def extract_metadata(ds: pydicom.dataset.FileDataset) -> dict:
    def get(tag, default=""):
        try:
            return str(ds.get(tag, default))
        except Exception:
            return ""

    meta = {
        "PatientName": get((0x0010, 0x0010)),
        "PatientID": get((0x0010, 0x0020)),
        "StudyDate": get((0x0008, 0x0020)),
        "SeriesDescription": get((0x0008, 0x103e)),
        "Modality": get((0x0008, 0x0060)),
    }
    return meta


def process_series(series_folder: Path, out_root: Path):
    slices = load_slices(series_folder)
    if not slices:
        logger.warning("No DICOM slices in %s", series_folder)
        return None
    # Extract metadata from first slice
    meta = extract_metadata(slices[0])
    # Create a subject code (de-identified) from folder name
    subject_code = f"sub-{series_folder.name}"
    series_out = out_root / subject_code
    series_out.mkdir(parents=True, exist_ok=True)

    # Save anonymized DICOMs
    anon_dir = series_out / "anonymized_dicoms"
    write_anonymized_dicoms(slices, anon_dir)

    # Try dcm2niix first
    nii_path = series_out / f"{subject_code}.nii.gz"
    if not try_dcm2niix(anon_dir, series_out):
        # Fallback: make a nifti from pixel arrays
        logger.info("Falling back to simple NIfTI writer for %s", series_folder.name)
        make_nifti_from_slices(slices, nii_path)

    mapping = {
        "original_path": str(series_folder.relative_to(ROOT)),
        "subject_code": subject_code,
        "series_description": meta.get("SeriesDescription", ""),
        "modality": meta.get("Modality", ""),
        "acquisition_date": meta.get("StudyDate", ""),
        "nii_path": str((series_out / nii_path.name).relative_to(ROOT)),
        "notes": "anonymized and converted",
    }
    return mapping


def main():
    series_list = find_series(RAW_DIR)
    rows = []
    for s in series_list:
        logger.info("Processing series: %s", s)
        mapping = process_series(s, OUT_DIR)
        if mapping:
            rows.append(mapping)

    if rows:
        df = pd.DataFrame(rows)
        out_xlsx = OUT_DIR / "mapping.xlsx"
        df.to_excel(out_xlsx, index=False)
        logger.info("Wrote mapping file: %s", out_xlsx)
    else:
        logger.info("No series processed. No mapping file created.")


if __name__ == "__main__":
    main()
