# Mapping Excel specification

The mapping Excel (`mapping.xlsx`) should contain one row per DICOM series converted. Suggested columns:

- original_path: path to the source DICOM folder (relative to repo root)
- subject_code: generated study-specific subject code (de-identified)
- series_description: DICOM SeriesDescription
- modality: DICOM Modality
- acquisition_date: shifted or relative acquisition date
- nii_path: path to generated `nii.gz` (relative to repo root)
- notes: any notes about conversion/anonymization

Store the mapping at `data/processed/mapping.xlsx`.
