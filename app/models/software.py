from datetime import datetime
from app.extensions import db

class FirmwareRelease(db.Model):
    __tablename__ = "firmware_releases"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    target_subsystem = db.Column(db.String(64), nullable=False)  # 'MCU Board (STM32)', 'Motor Driver (DSP)', 'Gateway Linux', 'BLE Sensor Hub'
    version = db.Column(db.String(32), nullable=False)  # 'v1.4.2-rc1'
    git_commit_hash = db.Column(db.String(40), nullable=False)  # 7-40 chars sha
    binary_checksum = db.Column(db.String(64), nullable=False)  # SHA-256
    release_type = db.Column(db.String(32), nullable=False, default="Release Candidate")  # 'Nightly', 'Alpha', 'Beta', 'Release Candidate', 'Production Stable'
    release_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="Testing")  # 'Development', 'Testing', 'Approved', 'Rejected', 'Deployed'
    created_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "target_subsystem": self.target_subsystem,
            "version": self.version,
            "git_commit_hash": self.git_commit_hash,
            "binary_checksum": self.binary_checksum,
            "release_type": self.release_type,
            "release_notes": self.release_notes,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class FlashRecord(db.Model):
    __tablename__ = "flash_records"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    unit_serial = db.Column(db.String(64), nullable=False)
    firmware_version = db.Column(db.String(32), nullable=False)
    subsystem = db.Column(db.String(64), nullable=False)
    flashed_by = db.Column(db.String(64), nullable=False)
    flashed_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_status = db.Column(db.String(32), nullable=False, default="Verified")  # 'Verified', 'CRC Mismatch', 'Flash Error'
    log_output = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "unit_serial": self.unit_serial,
            "firmware_version": self.firmware_version,
            "subsystem": self.subsystem,
            "flashed_by": self.flashed_by,
            "flashed_at": self.flashed_at.isoformat() if self.flashed_at else None,
            "verification_status": self.verification_status,
            "log_output": self.log_output,
        }

class SoftwareTestCase(db.Model):
    __tablename__ = "software_test_cases"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    test_suite = db.Column(db.String(64), nullable=False)  # 'Hardware-In-The-Loop (HIL)', 'CAN Bus Comms', 'Safety Watchdog', 'OTA Upgrade', 'Stress & Thermal'
    test_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    expected_result = db.Column(db.String(256), nullable=False)
    result = db.Column(db.String(32), nullable=False, default="Not Run")  # 'Not Run', 'In Progress', 'Passed', 'Failed', 'Blocked'
    is_critical = db.Column(db.Boolean, nullable=False, default=True)  # Stage gate check
    executed_by = db.Column(db.String(64), nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    execution_notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "test_suite": self.test_suite,
            "test_name": self.test_name,
            "description": self.description,
            "expected_result": self.expected_result,
            "result": self.result,
            "is_critical": self.is_critical,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_notes": self.execution_notes,
        }

