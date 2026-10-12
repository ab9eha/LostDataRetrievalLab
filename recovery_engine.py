
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

BASE_DIR = Path(__file__).resolve().parent
LAB_DIR = BASE_DIR / "lab_data"
ORIGINAL_DIR = LAB_DIR / "original_files"
DELETED_DIR = LAB_DIR / "simulated_deleted"
RECOVERED_DIR = LAB_DIR / "recovered_files"
EVIDENCE_DIR = BASE_DIR / "evidence"
MANIFEST_PATH = EVIDENCE_DIR / "original_manifest.json"
LOG_PATH = EVIDENCE_DIR / "recovery_log.json"


def setup_directories():
    for directory in (
        ORIGINAL_DIR, DELETED_DIR, RECOVERED_DIR, EVIDENCE_DIR
    ):
        directory.mkdir(parents=True, exist_ok=True)


def sha256_file(file_path):
    digest = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_json(path, default):
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )


def add_log(action, message, filename=""):
    logs = load_json(LOG_PATH, [])
    logs.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "filename": filename,
        "message": message
    })
    save_json(LOG_PATH, logs)


def create_test_files():
    setup_directories()

    samples = {
        "incident_notes.txt": (
            "Training evidence: suspicious login attempts were observed "
            "during a fictional security exercise.\n"
        ),
        "recovery_plan.txt": (
            "Recovery objective: restore test data and verify file integrity.\n"
        ),
        "case_summary.txt": (
            "Case ID: LDR-001\n"
            "This is synthetic data created for a safe recovery lab.\n"
        )
    }

    created = []

    for filename, content in samples.items():
        path = ORIGINAL_DIR / filename
        path.write_text(content, encoding="utf-8")
        created.append({
            "filename": filename,
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size
        })

    save_json(MANIFEST_PATH, created)
    add_log(
        "CREATE",
        f"Created {len(created)} disposable sample files."
    )

    return created


def simulate_deletion():
    setup_directories()

    files = [
        path for path in ORIGINAL_DIR.iterdir()
        if path.is_file()
    ]

    if not files:
        return 0

    moved = 0

    for source in files:
        destination = DELETED_DIR / source.name

        if destination.exists():
            destination = DELETED_DIR / (
                f"{source.stem}_{datetime.now().strftime('%H%M%S%f')}"
                f"{source.suffix}"
            )

        # Simulation only: move the file to a lab folder.
        # Nothing is permanently deleted from the storage device.
        shutil.move(str(source), str(destination))
        add_log(
            "SIMULATED DELETE",
            "Moved sample into simulated-deleted folder; "
            "the file remains intact.",
            source.name
        )
        moved += 1

    return moved


def recover_test_files():
    setup_directories()
    manifest = load_json(MANIFEST_PATH, [])
    recovered = []

    for source in DELETED_DIR.iterdir():
        if not source.is_file():
            continue

        destination = RECOVERED_DIR / source.name

        # Preserve any previous recovered copy.
        if destination.exists():
            destination = RECOVERED_DIR / (
                f"{source.stem}_{datetime.now().strftime('%H%M%S%f')}"
                f"{source.suffix}"
            )

        shutil.copy2(source, destination)
        recovered_hash = sha256_file(destination)

        original = next(
            (
                item for item in manifest
                if item["filename"] == source.name
            ),
            None
        )

        # A renamed duplicate may not match by filename.
        if original is None:
            original = next(
                (
                    item for item in manifest
                    if item["sha256"] == recovered_hash
                ),
                None
            )

        matches = (
            original is not None
            and original["sha256"] == recovered_hash
        )

        result = {
            "filename": source.name,
            "recovered_path": str(destination.relative_to(BASE_DIR)),
            "sha256": recovered_hash,
            "integrity": "PASS" if matches else "UNVERIFIED",
            "size_bytes": destination.stat().st_size
        }
        recovered.append(result)

        add_log(
            "RECOVER COPY",
            f"Created recovery copy; integrity: {result['integrity']}.",
            source.name
        )

    return recovered


def get_status():
    setup_directories()

    return {
        "Original files": sum(
            p.is_file() for p in ORIGINAL_DIR.iterdir()
        ),
        "Simulated deleted": sum(
            p.is_file() for p in DELETED_DIR.iterdir()
        ),
        "Recovered copies": sum(
            p.is_file() for p in RECOVERED_DIR.iterdir()
        )
    }


def get_logs():
    return load_json(LOG_PATH, [])


def build_report():
    return {
        "project": "Lost Data Retrieval Lab",
        "report_generated_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "experiment_type": "Safe simulated file deletion and copy recovery",
        "warning": (
            "This report documents a simulation, not a real disk-recovery "
            "operation. No files were permanently deleted by this lab."
        ),
        "status": get_status(),
        "original_manifest": load_json(MANIFEST_PATH, []),
        "recovery_log": get_logs()
    }
