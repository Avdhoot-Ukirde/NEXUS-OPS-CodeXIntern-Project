from datetime import datetime
from app.extensions import db

class PhysicalUnit(db.Model):
    __tablename__ = "physical_units"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    serial_number = db.Column(db.String(64), unique=True, nullable=False, index=True)  # 'AMR-SN-2026-001'
    batch_number = db.Column(db.String(64), nullable=False, default="BATCH-A")
    variant = db.Column(db.String(64), nullable=False, default="Rev B Production")
    build_stage = db.Column(db.String(32), nullable=False, default="SMT Pick-and-Place")  # 'Not Started', 'SMT Assembly', 'Through-Hole', 'Mechanical Fit', 'Harness Routing', 'Validation Passed', 'Scrapped'
    assigned_technician = db.Column(db.String(64), nullable=False, default="Lead Assembly Tech")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    traveler_steps = db.relationship("AssemblyTravelerStep", backref="unit", cascade="all, delete-orphan", lazy="dynamic", order_by="AssemblyTravelerStep.step_order.asc()")
    defects = db.relationship("AssemblyDefect", backref="unit", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self, include_steps=True):
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "serial_number": self.serial_number,
            "batch_number": self.batch_number,
            "variant": self.variant,
            "build_stage": self.build_stage,
            "assigned_technician": self.assigned_technician,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "defects_count": self.defects.count(),
        }
        if include_steps:
            data["traveler_steps"] = [step.to_dict() for step in self.traveler_steps.all()]
        return data

class AssemblyTravelerStep(db.Model):
    __tablename__ = "assembly_traveler_steps"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("physical_units.id", ondelete="CASCADE"), nullable=False, index=True)
    step_order = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    technician = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="Pending")  # 'Pending', 'In Progress', 'Passed', 'Failed', 'Rework'
    inspection_criteria = db.Column(db.String(256), nullable=True)
    measured_values = db.Column(db.String(256), nullable=True)  # e.g. "3.32V (tol ±2%), 12.04V, 5.01V, Torque 1.8 N*m"
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "step_order": self.step_order,
            "name": self.name,
            "technician": self.technician,
            "status": self.status,
            "inspection_criteria": self.inspection_criteria,
            "measured_values": self.measured_values,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
        }

class AssemblyDefect(db.Model):
    __tablename__ = "assembly_defects"

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey("physical_units.id", ondelete="CASCADE"), nullable=False, index=True)
    defect_type = db.Column(db.String(64), nullable=False)  # 'Cold Solder Joint', 'Short Circuit', 'Misaligned BGA', 'Stripped Screw', 'Harness Pinch'
    severity = db.Column(db.String(32), nullable=False, default="Medium")  # 'Minor', 'Major', 'Critical'
    description = db.Column(db.Text, nullable=False)
    disposition = db.Column(db.String(64), nullable=False, default="Pending")  # 'Pending', 'Reworked & Retested', 'Scrapped', 'Use As-Is'
    logged_by = db.Column(db.String(64), nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "unit_id": self.unit_id,
            "defect_type": self.defect_type,
            "severity": self.severity,
            "description": self.description,
            "disposition": self.disposition,
            "logged_by": self.logged_by,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

