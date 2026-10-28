# CSC-F-012: Clinical Safety Case Report (DCB0129)
**Project:** `csc-dicom-safety-pipeline` | **Version:** 1.0.0 | **Date:** October 2026

## 1. Executive Summary & Safety Claim
We claim that `csc-dicom-safety-pipeline` reduces the risk of (a) unauthorized Patient Identifiable Information (PHI) leakage and (b) silent corruption of quantitative CT physics metadata (`PixelSpacing`, `SliceThickness`, `RescaleSlope`, `RescaleIntercept`) to an acceptable level (**Residual Risk Score <= 4 across all 15 identified hazards in `CSC-F-013`**).

## 2. Summary of Deterministic Engineering Controls & Test Evidence
1. **Strict Allow-List Enforcement (`PS315_ALLOWLIST_POLICY`):** Replaces error-prone block-lists by stripping all unapproved tags and all odd-group vendor private tags (`group % 2 == 1`).
2. **Stage 5 Blocking Leak Validator Gate (`stage5_leak_validator_gate`):** Re-reads the serialized output file from disk using recursive `ds.walk()` and physically deletes (`unlink()`) any file containing residual PHI, odd private tags, or missing `PatientIdentityRemoved == "YES"` markers prior to Orthanc network transmission.
3. **Automated CI Verification (`tests/test_safety_gate.py`):** Verified on every commit via GitHub Actions against deliberately planted PHI leaks (`HAZ-01` to `HAZ-15`).

## 3. What Would Be Required Before Touching Real NHS Patient Data
1. Formal **Data Protection Impact Assessment (DPIA)** and **Caldicott Guardian** approval within the NHS Trust.
2. Hardware Security Module (HSM) or Kubernetes Secret management for the HMAC-SHA256 `secret_salt` (stored on an air-gapped Trust VLAN).
3. Optical Character Recognition (OCR) pixel-scrubbing gate for modalities with burned-in pixel annotations (Ultrasound / Secondary Capture).
4. Local **DCB0160** Clinical Risk Management sign-off by the receiving NHS Trust's appointed Clinical Safety Officer (CSO).
