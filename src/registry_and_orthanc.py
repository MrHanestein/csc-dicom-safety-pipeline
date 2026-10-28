import base64
import json
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from src.pipeline import stage5_leak_validator_gate

class StudyRegistry:
    def __init__(self, db_path: str = "study_registry.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS study_registry (
                input_sha256 TEXT PRIMARY KEY,
                patient_pseudonym TEXT NOT NULL,
                deid_study_uid TEXT NOT NULL,
                status TEXT NOT NULL,
                registered_at_utc TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def register_study_idempotent(self, input_sha256: str, pseudonym: str, deid_study_uid: str, status: str) -> bool:
        cursor = self.conn.execute("SELECT 1 FROM study_registry WHERE input_sha256 = ?", (input_sha256,))
        if cursor.fetchone() is not None:
            return False
        self.conn.execute(
            "INSERT INTO study_registry VALUES (?, ?, ?, ?, ?)",
            (input_sha256, pseudonym, deid_study_uid, status, datetime.now(timezone.utc).isoformat())
        )
        self.conn.commit()
        return True

    def count_studies(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM study_registry").fetchone()[0]

def upload_verified_dicom_to_orthanc(
    deid_filepath: Path,
    forbidden_strings: list[str],
    orthanc_url: str = "http://127.0.0.1:8042/instances",
    username: str = "orthanc",
    password: str = "orthanc"
) -> dict:
    is_safe, violations = stage5_leak_validator_gate(deid_filepath, forbidden_strings)
    if not is_safe:
        raise PermissionError(f"HAZ-09 BLOCK: Refusing Orthanc upload! Violations: {violations}")

    dicom_bytes = deid_filepath.read_bytes()
    req = urllib.request.Request(orthanc_url, data=dicom_bytes, method="POST")
    req.add_header("Content-Type", "application/dicom")
    b64_auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {b64_auth}")

    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))
