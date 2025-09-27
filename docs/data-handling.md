# Data handling and de-identification

This project processes medical DICOM (DCM) files. Follow these rules:

- Place raw DICOM data under `data/raw/`.
- Processed outputs (anonymized DICOMs, `nii.gz`, mapping Excel) go under `data/processed/`.
- Never commit `data/raw/` or `data/processed/` — these are listed in `.gitignore`.

De-identification checklist:

1. Remove or replace patient-identifying DICOM tags (PatientName, PatientID, PatientBirthDate, etc.).
2. Keep non-identifying metadata required for research (StudyDate may be shifted to a relative offset).
3. Log actions and store the mapping in `data/processed/mapping.xlsx`.
4. Only share processed `nii.gz` and the mapping file after sign-off.
