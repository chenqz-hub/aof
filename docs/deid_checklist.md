# De-identification checklist

Follow this checklist before sharing any outputs derived from DICOM data.

1. Inventory: list all data sources and owners.
2. Minimize: only keep DICOM tags required for analysis.
3. Remove direct identifiers: PatientName, PatientID, PatientBirthDate, ReferringPhysicianName, etc.
4. Date handling: shift dates consistently per subject or remove StudyDate if not needed.
5. Visual inspection: inspect images for burned-in annotations.
6. Logging: keep a secure log of original->de-identified mapping (store in a protected location).
7. Approval: obtain study PI or data governance sign-off before sharing.
