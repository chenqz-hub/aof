# DICOM to de-identified NIfTI converter (aof)

Purpose: convert DICOM (DCM) files to de-identified NIfTI (`.nii.gz`) and extract metadata into a mapping Excel file.

Directory layout

- data/
	- raw/           # Place source DICOM series here (one series per subfolder)
	- processed/     # Outputs: anonymized DICOMs, nii.gz, mapping.xlsx
- docs/            # Project documentation and specs
- scripts/         # Conversion and utility scripts

Quickstart

1. Put your DICOM series into `data/raw/`. Create one folder per series, e.g. `data/raw/subject001_series1/`.
2. Create and activate a Python virtual environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

3. Run the conversion script:

```powershell
python scripts\convert_dcm.py
```

Notes

- The script will attempt to use `dcm2niix` if available on PATH to generate `nii.gz` files. If not found, it will fall back to a simple NIfTI writer.
- Raw and processed data directories are excluded from git via `.gitignore` — do not commit PHI.

See `docs/data-handling.md` and `docs/mapping_spec.md` for more details on de-identification and mapping format.
