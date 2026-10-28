# CSC-F-009: Clinical Risk Management Plan (DCB0129 Compliant)
**Project:** DICOM Clinical Data Safety & De-Identification Pipeline (`csc-dicom-safety-pipeline`)  
**Standard:** NHS England DCB0129 / ISO 14971 / IEC 62304 (Software Safety Classification: Class B)  
**Template Reference:** Adapted from Guy's and St Thomas' NHS Foundation Trust (`GSTT-CSC`) QMS (`CSC-F-009`, Apache-2.0)

## 1. Scope & Intended Use
This software is an open-source research and training prototype that de-identifies volumetric CT DICOM imaging studies in accordance with **DICOM PS3.15 Annex E (Table E.1-1)** and validates output integrity before archival in an Orthanc PACS server.
> **REGULATORY BOUNDARY:** This software is a **Research & Training Prototype — NOT FOR CLINICAL DIAGNOSTIC USE**. Before deployment on live NHS patient data, local Trust Information Governance (Caldicott Guardian), DPIA sign-off, and a host-organization **DCB0160** deployment safety case are mandatory.

## 2. Clinical Risk Management Governance & Roles
- **Clinical Safety Officer (CSO) Role (Simulated for STP Portfolio):** Oversees Hazard Log (`CSC-F-013`), approves risk acceptability criteria, and signs off `CSC-F-012` Safety Case Report.
- **Verification Gate Rule:** No hazard mitigation may rely solely on human visual inspection where a deterministic automated `pytest` control can be enforced in CI/CD.

## 3. Risk Evaluation Matrix (5x5 NHS DCB0129 Matrix)
- **Severity (1–5):** 1 = Negligible, 2 = Minor, 3 = Moderate (Single IG breach / reversible delay), 4 = Major (Systemic PHI breach or corrupted clinical cohort physics), 5 = Catastrophic.
- **Likelihood (1–5):** 1 = Very Unlikely (Automated blocking gate in place), 2 = Unlikely, 3 = Possible, 4 = Likely, 5 = Frequent.
