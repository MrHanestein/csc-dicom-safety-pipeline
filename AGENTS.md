# AGENTS.md — Mandatory Clinical Safety & Engineering Laws for AI Coding Agents

Whenever you inspect, modify, or extend any file in this repository, you MUST obey these 5 deterministic laws:

1. **STRICT ALLOW-LIST ONLY (`PS315_ALLOWLIST_POLICY`):** Never introduce a block-list. Any DICOM tag not explicitly in `PS315_ALLOWLIST_POLICY` must be removed (`X`).
2. **RECURSIVE WALK MANDATE (`ds.walk()`):** Always use `ds.remove_private_tags()` and `ds.walk()` in both Stage 4 (`recursive_clean_with_walk`) and Stage 5 (`stage5_leak_validator_gate`) so odd-group private tags (`group % 2 == 1`) and nested Sequence (`VR == 'SQ'`) PHI are caught at all depths.
3. **CT PHYSICS PRESERVATION:** Never remove or alter Action Code `K` tags required for quantitative Hounsfield Unit or 3D volumetric math (`PixelSpacing`, `SliceThickness`, `RescaleSlope`, `RescaleIntercept`).
4. **PLUG-AND-SOCKET CONTRACT SAFETY:** Never change the input parameters or return type of existing functions without using default parameter values (`param=default`) so downstream callers never break.
5. **MANDATORY VERIFICATION GATE:** After any code edit, you MUST run `$env:PYTHONPATH="."; pytest -v -W error::DeprecationWarning` and verify 100% passing tests before finishing.
