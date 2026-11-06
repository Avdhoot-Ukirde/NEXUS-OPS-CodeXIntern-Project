from datetime import datetime
from app.extensions import db

class DesignDoc(db.Model):
    __tablename__ = "design_docs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(128), nullable=False)
    doc_type = db.Column(db.String(64), nullable=False)  # 'Schematic', 'PCB Layout', 'Mechanical CAD', 'Wiring Harness', 'Architecture Spec'
    subsystem = db.Column(db.String(64), nullable=False)  # 'Main Controller', 'Power Board', 'Chassis', 'Sensor Array'
    version = db.Column(db.String(32), nullable=False, default="Rev 1.0")
    file_url = db.Column(db.String(256), nullable=True)
    status = db.Column(db.String(32), nullable=False, default="Under Review")  # 'Draft', 'Under Review', 'Approved', 'Rejected'
    author = db.Column(db.String(64), nullable=False)
    approved_by = db.Column(db.String(64), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "subsystem": self.subsystem,
            "version": self.version,
            "file_url": self.file_url,
            "status": self.status,
            "author": self.author,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class EngineeringChangeOrder(db.Model):
    __tablename__ = "engineering_change_orders"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    eco_number = db.Column(db.String(32), unique=True, nullable=False, index=True)  # e.g., 'ECO-2026-004'
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reason = db.Column(db.String(64), nullable=False)  # 'Component Obsolescence', 'Thermal Issue', 'EMI/EMC Compliance', 'Cost Reduction'
    severity = db.Column(db.String(32), nullable=False, default="Medium")  # 'Low', 'Medium', 'High', 'Critical'
    affected_subsystems = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="Proposed")  # 'Proposed', 'In Review', 'Approved', 'Implemented', 'Closed'
    requested_by = db.Column(db.String(64), nullable=False)
    approved_by = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "eco_number": self.eco_number,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "severity": self.severity,
            "affected_subsystems": self.affected_subsystems,
            "status": self.status,
            "requested_by": self.requested_by,
            "approved_by": self.approved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

