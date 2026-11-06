from datetime import datetime
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.project import Project
from app.models.software import FirmwareRelease, SoftwareTestCase, FlashRecord
from app.schemas.project_schemas import (
    FirmwareReleaseCreateSchema,
    TestCaseUpdateSchema,
    FlashRecordCreateSchema,
)
from app.services.audit_service import log_activity

api_software_bp = Blueprint("api_software", __name__, url_prefix="/api/v1")

@api_software_bp.route("/projects/<int:project_id>/firmware", methods=["GET"])
def get_firmware(project_id):
    project = Project.query.get_or_404(project_id)
    releases = project.firmware_releases.order_by(FirmwareRelease.created_at.desc()).all()
    flashes = FlashRecord.query.filter_by(project_id=project.id).order_by(FlashRecord.flashed_at.desc()).all()
    return jsonify({
        "releases": [r.to_dict() for r in releases],
        "flashes": [f.to_dict() for f in flashes],
    })

@api_software_bp.route("/projects/<int:project_id>/firmware", methods=["POST"])
def create_firmware(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = FirmwareReleaseCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    release = FirmwareRelease(
        project_id=project.id,
        target_subsystem=schema.target_subsystem,
        version=schema.version,
        git_commit_hash=schema.git_commit_hash,
        binary_checksum=schema.binary_checksum,
        release_type=schema.release_type,
        release_notes=schema.release_notes,
        status="Testing",
        created_by=schema.created_by
    )
    db.session.add(release)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Software",
        action="FIRMWARE_RELEASED",
        description=f"Firmware {release.version} ({release.target_subsystem}) released for testing (Commit: {release.git_commit_hash[:7]}).",
        performed_by=schema.created_by
    )

    return jsonify(release.to_dict()), 201

@api_software_bp.route("/projects/<int:project_id>/tests", methods=["GET"])
def get_tests(project_id):
    project = Project.query.get_or_404(project_id)
    tests = project.test_cases.order_by(SoftwareTestCase.is_critical.desc(), SoftwareTestCase.id.asc()).all()
    
    total = len(tests)
    passed = len([t for t in tests if t.result == "Passed"])
    failed = len([t for t in tests if t.result == "Failed"])
    not_run = len([t for t in tests if t.result == "Not Run"])
    pass_pct = (passed / total * 100) if total > 0 else 0.0

    return jsonify({
        "tests": [t.to_dict() for t in tests],
        "metrics": {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "not_run": not_run,
            "pass_pct": round(pass_pct, 1),
        }
    })

@api_software_bp.route("/projects/<int:project_id>/tests", methods=["POST"])
def add_test(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    
    test = SoftwareTestCase(
        project_id=project.id,
        test_suite=data.get("test_suite", "Hardware-In-The-Loop (HIL)"),
        test_name=data.get("test_name", "Subsystem Functional Test"),
        description=data.get("description", ""),
        expected_result=data.get("expected_result", "Nominal telemetry"),
        is_critical=data.get("is_critical", True),
        result="Not Run"
    )
    db.session.add(test)
    db.session.commit()
    return jsonify(test.to_dict()), 201

@api_software_bp.route("/tests/<int:test_id>", methods=["PUT"])
def update_test(test_id):
    test = SoftwareTestCase.query.get_or_404(test_id)
    try:
        data = request.get_json() or {}
        schema = TestCaseUpdateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    test.result = schema.result
    test.executed_by = schema.executed_by
    test.executed_at = datetime.utcnow()
    if schema.execution_notes is not None:
        test.execution_notes = schema.execution_notes

    db.session.commit()

    log_activity(
        project_id=test.project_id,
        stage="Software",
        action="TEST_EXECUTED",
        description=f"Test '{test.test_name}' marked as '{test.result}' by {schema.executed_by}.",
        performed_by=schema.executed_by,
        details=schema.execution_notes
    )

    return jsonify(test.to_dict())

@api_software_bp.route("/projects/<int:project_id>/flash", methods=["POST"])
def log_flash(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        data = request.get_json() or {}
        schema = FlashRecordCreateSchema(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    record = FlashRecord(
        project_id=project.id,
        unit_serial=schema.unit_serial,
        firmware_version=schema.firmware_version,
        subsystem=schema.subsystem,
        flashed_by=schema.flashed_by,
        verification_status=schema.verification_status,
        log_output=schema.log_output or "Target MCU programmed via SWD/JTAG. Memory flash address 0x08000000 verified. Checksum matched."
    )
    db.session.add(record)
    db.session.commit()

    log_activity(
        project_id=project.id,
        stage="Software",
        action="FIRMWARE_FLASHED",
        description=f"Unit {record.unit_serial} flashed with {record.firmware_version} ({record.verification_status}).",
        performed_by=schema.flashed_by
    )

    return jsonify(record.to_dict()), 201

