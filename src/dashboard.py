import json
from pathlib import Path

def generate_html_audit_dashboard(audit_log_path: Path, output_html_path: Path) -> Path:
    records = []
    if audit_log_path.exists():
        for line in audit_log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))

    total = len(records)
    verified = sum(1 for r in records if r["status"] == "VERIFIED_SAFE")
    blocked = sum(1 for r in records if r["status"] != "VERIFIED_SAFE")

    rows_html = ""
    for r in records:
        badge_color = "#16a34a" if r["status"] == "VERIFIED_SAFE" else "#dc2626"
        violations_str = ", ".join(r["violations_detected"]) or "None (All PS3.15 Checks Passed)"
        rows_html += f"""
        <tr>
            <td>{r['timestamp_utc']}</td>
            <td><strong>{r['input_file']}</strong></td>
            <td><code>{r['input_sha256'][:12]}...</code></td>
            <td><code>{(r['output_sha256'] or 'DELETED_BY_GATE')[:16]}</code></td>
            <td style="color: white; background: {badge_color}; font-weight: bold;">{r['status']}</td>
            <td>{violations_str}</td>
        </tr>"""

    html_content = f"""<!DOCTYPE html>
    <html><head><title>CSC STP DICOM Safety Pipeline — Audit Dashboard</title>
    <style>
        body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }}
        .banner {{ background: #fef3c7; border-left: 6px solid #d97706; padding: 1rem; margin-bottom: 1.5rem; }}
        .cards {{ display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }}
        .card {{ background: white; padding: 1.2rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; }}
        table {{ width: 100%; border-collapse: collapse; background: white; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 0.75rem; text-align: left; font-size: 0.9rem; }}
        th {{ background: #1e293b; color: white; }}
    </style></head><body>
        <div class="banner"><strong>REGULATORY NOTICE (NHS DCB0129 / HAZ-15):</strong> Research & Training Prototype — NOT FOR CLINICAL DIAGNOSTIC USE.</div>
        <h1>CSC DICOM De-Identification & Stage 5 Safety Gate Dashboard</h1>
        <div class="cards">
            <div class="card"><h3>Total Studies Processed</h3><h2>{total}</h2></div>
            <div class="card"><h3 style="color:#16a34a;">Verified Safe (Passed Stage 5)</h3><h2>{verified}</h2></div>
            <div class="card"><h3 style="color:#dc2626;">Blocked & Deleted (PHI Leak Caught)</h3><h2>{blocked}</h2></div>
        </div>
        <table>
            <thead><tr><th>UTC Timestamp</th><th>File</th><th>Input SHA-256</th><th>Output SHA-256</th><th>Stage 5 Gate Status</th><th>Violations Logged</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </body></html>"""

    output_html_path.write_text(html_content, encoding="utf-8")
    return output_html_path
