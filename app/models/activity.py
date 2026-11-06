from datetime import datetime
from app.extensions import db

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = db.Column(db.String(32), nullable=False)  # 'Design', 'Purchase', 'Assembly', 'Software', 'Dispatch', 'System'
    action = db.Column(db.String(64), nullable=False)  # 'STAGE_TRANSITION', 'CAD_APPROVED', 'BOM_RECEIVED', 'FLASH_VERIFIED', etc.
    description = db.Column(db.String(256), nullable=False)
    performed_by = db.Column(db.String(64), nullable=False, default="System")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    details = db.Column(db.Text, nullable=True)  # JSON or detail string

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "stage": self.stage,
            "action": self.action,
            "description": self.description,
            "performed_by": self.performed_by,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "details": self.details,
        }

