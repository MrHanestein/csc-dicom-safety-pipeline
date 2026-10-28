import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, UID

PS315_ALLOWLIST_POLICY = {
    (0x0010, 0x0010): ("Z", "PatientName"),
    (0x0010, 0x0020): ("C", "PatientID"),
    (0x0010, 0x0030): ("Z", "PatientBirthDate"),
    (0x0010, 0x0040): ("Z", "PatientSex"),
    (0x0008, 0x0016): ("K", "SOPClassUID"),
    (0x0008, 0x0018): ("U", "SOPInstanceUID"),
    (0x0008, 0x0020): ("Z", "StudyDate"),
    (0x0008, 0x0030): ("Z", "StudyTime"),
    (0x0008, 0x0050): ("Z", "AccessionNumber"),
    (0x0008, 0x0060): ("K", "Modality"),
    (0x0008, 0x0070): ("D", "Manufacturer"),
    (0x0020, 0x000D): ("U", "StudyInstanceUID"),
    (0x0020, 0x000E): ("U", "SeriesInstanceUID"),
    (0x0020, 0x0010): ("Z", "StudyID"),
    (0x0020, 0x0011): ("K", "SeriesNumber"),
    (0x0020, 0x0013): ("K", "InstanceNumber"),
    (0x0018, 0x0050): ("K", "SliceThickness"),
    (0x0028, 0x0002): ("K", "SamplesPerPixel"),
    (0x0028, 0x0004): ("K", "PhotometricInterpretation"),
    (0x0028, 0x0010): ("K", "Rows"),
    (0x0028, 0x0011): ("K", "Columns"),
    (0x0028, 0x0030): ("K", "PixelSpacing"),
    (0x0028, 0x0100): ("K", "BitsAllocated"),
    (0x0028, 0x0101): ("K", "BitsStored"),
    (0x0028, 0x0102): ("K", "HighBit"),
    (0x0028, 0x0103): ("K", "PixelRepresentation"),
    (0x0028, 0x1052): ("K", "RescaleIntercept"),
    (0x0028, 0x1053): ("K", "RescaleSlope"),
    (0x7FE0, 0x0010): ("K", "PixelData"),
    (0x0012, 0x0062): ("D", "PatientIdentityRemoved"),
    (0x0012, 0x0063): ("D", "DeidentificationMethod"),
}

def deterministic_uid(old_uid: str, secret_salt: str) -> UID:
    clean_old = str(old_uid).strip()
    digest = hmac.new(secret_salt.encode("utf-8"), clean_old.encode("utf-8"), hashlib.sha256).digest()
    int_128 = int.from_bytes(digest[:16], byteorder="big")
    return UID(f"2.25.{int_128}")

def deterministic_pseudonym(raw_id: str, secret_salt: str, length: int = 12) -> str:
    digest = hmac.new(secret_salt.encode("utf-8"), str(raw_id).strip().encode("utf-8"), hashlib.sha256).hexdigest()
    return f"ANON-{digest[:length].upper()}"

def create_synthetic_hospital_dicom(
    filepath: Path,
    patient_name: str = "SMITH^JOHN",
    patient_id: str = "NHS-998877"
) -> Path:
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = UID("1.2.840.10008.5.1.4.1.1.2")
    file_meta.MediaStorageSOPInstanceUID = UID("1.2.826.0.1.3680043.2.1125.1.99999")
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.file_meta = file_meta

    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.PatientBirthDate = "19850412"
    ds.PatientSex = "M"
    ds.InstitutionName = "St Thomas Hospital London"
    ds.ReferringPhysicianName = "DR^HOUSE^GREGORY"

    ds.add_new((0x0009, 0x0010), "LO", "SIEMENS_SECRET_CREATOR")
    ds.add_new((0x0009, 0x1001), "LO", f"LEAKED_NOTE_FOR_{patient_name}")

    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = UID("1.2.826.0.1.3680043.2.1125.2.11111")
    ds.SeriesInstanceUID = UID("1.2.826.0.1.3680043.2.1125.3.22222")
    ds.StudyDate = "20261018"
    ds.StudyTime = "143000"
    ds.AccessionNumber = "ACC-2026-555"
    ds.Modality = "CT"
    ds.Manufacturer = "SIEMENS"
    ds.StudyID = "STUDY-001"
    ds.SeriesNumber = 1
    ds.InstanceNumber = 1

    ds.SliceThickness = "1.5"
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 4
    ds.Columns = 4
    ds.PixelSpacing = ["0.8", "0.8"]
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1
    ds.RescaleIntercept = "-1024.0"
    ds.RescaleSlope = "1.0"
    ds.PixelData = np.full((4, 4), 1064, dtype=np.int16).tobytes()

    ds.save_as(filepath, enforce_file_format=True)
    return filepath

def recursive_clean_with_walk(ds: Dataset, secret_salt: str) -> None:
    ds.remove_private_tags()

    def _clean_element(curr_ds: Dataset, elem: pydicom.DataElement) -> None:
        tag_tuple = (elem.tag.group, elem.tag.element)
        if elem.VR == "SQ":
            if tag_tuple not in PS315_ALLOWLIST_POLICY:
                del curr_ds[elem.tag]
            return
        if tag_tuple not in PS315_ALLOWLIST_POLICY:
            del curr_ds[elem.tag]
            return
        action, _ = PS315_ALLOWLIST_POLICY[tag_tuple]
        if action == "Z":
            elem.value = ""
        elif action == "D" and tag_tuple == (0x0008, 0x0070):
            elem.value = "ANON_VENDOR"
        elif action == "C":
            elem.value = deterministic_pseudonym(elem.value, secret_salt)
        elif action == "U":
            elem.value = deterministic_uid(elem.value, secret_salt)

    ds.walk(_clean_element)

def deidentify_dicom_stage1_to_4(input_path: Path, output_path: Path, secret_salt: str) -> Dataset:
    ds = pydicom.dcmread(input_path)
    recursive_clean_with_walk(ds, secret_salt)

    ds.PatientIdentityRemoved = "YES"
    ds.DeidentificationMethod = "PS3.15_Annex_E_AllowList_Profile"
    ds.file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID

    ds.save_as(output_path, enforce_file_format=True)
    return ds

def stage5_leak_validator_gate(
    deid_filepath: Path,
    forbidden_strings: list[str],
    allowlist_policy: dict = PS315_ALLOWLIST_POLICY
) -> tuple[bool, list[str]]:
    violations = []
    ds = pydicom.dcmread(deid_filepath)

    def _inspect_element(curr_ds: Dataset, elem: pydicom.DataElement) -> None:
        tag_tuple = (elem.tag.group, elem.tag.element)
        if elem.tag.group % 2 == 1:
            violations.append(f"HAZARD-PRIV-TAG: Private odd-group tag {tag_tuple} survived!")
        if elem.VR != "SQ":
            if tag_tuple not in allowlist_policy:
                violations.append(f"HAZARD-UNAPPROVED-TAG: Tag {tag_tuple} ({elem.name}) is not on allow-list!")
            else:
                action, keyword = allowlist_policy[tag_tuple]
                if action == "Z" and str(elem.value).strip() != "":
                    violations.append(f"HAZARD-NONEMPTY-Z: Tag {keyword} {tag_tuple} must be blank!")
            if tag_tuple != (0x7FE0, 0x0010):
                val_str = str(elem.value).upper()
                for secret in forbidden_strings:
                    if secret and len(secret) >= 3 and secret.upper() in val_str:
                        violations.append(
                            f"HAZARD-PHI-LEAK: Forbidden string '{secret}' leaked inside {elem.name} {tag_tuple}!"
                        )

    ds.walk(_inspect_element)

    if getattr(ds, "PatientIdentityRemoved", "") != "YES":
        violations.append("HAZARD-MISSING-MARKER: PatientIdentityRemoved (0012,0062) is not 'YES'!")

    return (len(violations) == 0), violations

def run_pipeline_with_audit_log(
    input_path: Path,
    output_path: Path,
    audit_log_path: Path,
    secret_salt: str = "GSTT_CSC_SALT_2026"
) -> dict:
    raw_ds = pydicom.dcmread(input_path)
    forbidden_phi = [
        str(getattr(raw_ds, "PatientName", "")),
        str(getattr(raw_ds, "PatientID", "")),
        str(getattr(raw_ds, "InstitutionName", "")),
        str(getattr(raw_ds, "ReferringPhysicianName", "")),
    ]

    with open(input_path, "rb") as f:
        input_sha256 = hashlib.file_digest(f, "sha256").hexdigest()

    deidentify_dicom_stage1_to_4(input_path, output_path, secret_salt)
    passed_gate, violations = stage5_leak_validator_gate(output_path, forbidden_phi)

    if not passed_gate:
        if output_path.exists():
            output_path.unlink()
        status = "BLOCKED_BY_STAGE5_GATE"
        output_sha256 = None
    else:
        status = "VERIFIED_SAFE"
        with open(output_path, "rb") as f:
            output_sha256 = hashlib.file_digest(f, "sha256").hexdigest()

    audit_record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(input_path.name),
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "status": status,
        "violations_detected": violations,
    }
    with open(audit_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_record) + "\n")

    return audit_record
