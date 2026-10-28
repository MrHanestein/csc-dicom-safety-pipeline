from pathlib import Path
import pydicom
from pydicom.sequence import Sequence
from src.pipeline import (
    create_synthetic_hospital_dicom,
    recursive_clean_with_walk,
    run_pipeline_with_audit_log,
    stage5_leak_validator_gate,
)
from src.registry_and_orthanc import StudyRegistry

def test_happy_path_deidentification_and_physics_preservation(tmp_path: Path):
    raw_dcm = create_synthetic_hospital_dicom(tmp_path / "raw.dcm", "JONES^GWEN", "NHS-123456")
    clean_dcm = tmp_path / "clean.dcm"
    audit_log = tmp_path / "audit.jsonl"

    result = run_pipeline_with_audit_log(raw_dcm, clean_dcm, audit_log)

    assert result["status"] == "VERIFIED_SAFE"
    assert result["violations_detected"] == []
    assert clean_dcm.exists()

    ds = pydicom.dcmread(clean_dcm)
    assert ds.PatientName == ""
    assert str(ds.PatientID).startswith("ANON-")
    assert (0x0009, 0x1001) not in ds
    assert "InstitutionName" not in ds
    assert float(ds.RescaleIntercept) == -1024.0
    assert [float(x) for x in ds.PixelSpacing] == [0.8, 0.8]

def test_stage5_gate_catches_deliberately_planted_leak(tmp_path: Path):
    raw_dcm = create_synthetic_hospital_dicom(tmp_path / "raw_leak.dcm", "EVANS^DAFYDD", "NHS-777888")

    is_safe, violations = stage5_leak_validator_gate(
        raw_dcm,
        forbidden_strings=["EVANS^DAFYDD", "NHS-777888", "St Thomas Hospital London"]
    )

    assert is_safe is False
    violation_text = " | ".join(violations)
    assert "HAZARD-PRIV-TAG" in violation_text
    assert "HAZARD-UNAPPROVED-TAG" in violation_text
    assert "HAZARD-NONEMPTY-Z" in violation_text
    assert "HAZARD-PHI-LEAK" in violation_text

def test_recursive_walk_catches_and_cleans_nested_sequence_phi(tmp_path: Path):
    nested_dcm_path = create_synthetic_hospital_dicom(
        tmp_path / "nested_leak.dcm",
        patient_name="WILLIAMS^RHYS",
        patient_id="NHS-555666"
    )
    ds = pydicom.dcmread(nested_dcm_path)

    sub_item = pydicom.Dataset()
    sub_item.PatientName = "WILLIAMS^RHYS"
    sub_item.add_new((0x0019, 0x1099), "LO", "HIDDEN_SIEMENS_NOTE_WILLIAMS^RHYS")
    ds.RequestAttributesSequence = Sequence([sub_item])
    ds.save_as(nested_dcm_path, enforce_file_format=True)

    is_safe_before, violations_before = stage5_leak_validator_gate(
        nested_dcm_path,
        forbidden_strings=["WILLIAMS^RHYS", "NHS-555666"]
    )
    assert is_safe_before is False
    assert any("WILLIAMS^RHYS" in v for v in violations_before)

    recursive_clean_with_walk(ds, secret_salt="GSTT_CSC_SALT_2026")
    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = "PS3.15_AllowList_Recursive_Walk"
    cleaned_nested_path = tmp_path / "nested_cleaned.dcm"
    ds.save_as(cleaned_nested_path, enforce_file_format=True)

    is_safe_after, violations_after = stage5_leak_validator_gate(
        cleaned_nested_path,
        forbidden_strings=["WILLIAMS^RHYS", "NHS-555666"]
    )
    assert is_safe_after is True
    assert violations_after == []

def test_week5_study_registry_is_strictly_idempotent(tmp_path: Path):
    db_file = str(tmp_path / "test_registry.sqlite")
    registry = StudyRegistry(db_path=db_file)

    assert registry.register_study_idempotent("sha256_scan_001", "ANON-112233", "2.25.987", "VERIFIED_SAFE") is True
    assert registry.register_study_idempotent("sha256_scan_001", "ANON-112233", "2.25.987", "VERIFIED_SAFE") is False
    assert registry.register_study_idempotent("sha256_scan_001", "ANON-112233", "2.25.987", "VERIFIED_SAFE") is False
    assert registry.count_studies() == 1
