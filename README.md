# CSC STP Flagship — DICOM Clinical Data Safety Pipeline (`PS3.15` + `DCB0129`)

![CI Status](https://github.com/MrHanestein/csc-dicom-safety-pipeline/actions/workflows/ci.yml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **INTENDED USE & REGULATORY DISCLAIMER:** This repository is an open-source Clinical Scientific Computing (CSC) engineering portfolio project demonstrating deterministic DICOM PS3.15 de-identification and NHS `DCB0129` risk engineering. **NOT FOR CLINICAL DIAGNOSTIC USE.**

## 1. System Architecture: Stage 5 Is a Blocking Gate, Not a Report
1. **Stages 1–4 (`src/pipeline.py`):** Ingests DICOM studies, strips odd-group vendor private tags (`group % 2 == 1`), applies a strict **DICOM PS3.15 Annex E (Table E.1-1)** allow-list (`K, Z, D, U, C` action codes) via recursive `ds.walk()`, generates deterministic `2.25.<128-bit>` UIDs, and preserves CT Hounsfield/Voxel physics (`PixelSpacing`, `SliceThickness`, `RescaleSlope`, `RescaleIntercept`).
2. **Stage 5 (`stage5_leak_validator_gate`):** Re-reads the saved file from disk and **blocks/deletes** any file where a single unapproved tag, odd private tag, or planted patient identifier survived.
3. **Stages 6–9 (`src/registry_and_orthanc.py`, `src/dashboard.py` & `docs/safety/`):** Records streaming SHA-256 input/output checksums to an immutable JSONL audit trail, enforces idempotent study registration, uploads verified files to **Orthanc PACS (`port 8042`)**, and links every control to a 15-row **NHS DCB0129 Hazard Log (`CSC-F-013`)**.

## 2. Clinical Risk If This Software Fails
1. **Information Governance & Patient Privacy Harm (`HAZ-01`, `HAZ-02`, `HAZ-03`, `HAZ-09`, `HAZ-13`):** If a block-list misses a vendor private tag (`0009,1001`) or a nested sequence attribute (`RequestAttributesSequence`), real patient identities leave the NHS Trust boundary—violating the UK GDPR, the Caldicott Principles, and patient trust.
2. **Silent Quantitative Physics Corruption (`HAZ-04`, `HAZ-05`, `HAZ-06`):** If an overly aggressive anonymizer strips `PixelSpacing (0028,0030)`, `SliceThickness (0018,0050)`, or `RescaleIntercept (0028,1052)`, downstream radiological tools and medical AI models compute false organ volumes or invalid tissue radiodensities.

## 3. NHS DCB0129 Safety Documentation (Adapted from GSTT-CSC QMS, Apache-2.0)
- [`docs/safety/CSC-F-009-Clinical-Risk-Management-Plan.md`](docs/safety/CSC-F-009-Clinical-Risk-Management-Plan.md)
- [`docs/safety/CSC-F-013-Hazard-Log.md`](docs/safety/CSC-F-013-Hazard-Log.md)
- [`docs/safety/CSC-F-012-Clinical-Safety-Case-Report.md`](docs/safety/CSC-F-012-Clinical-Safety-Case-Report.md)
