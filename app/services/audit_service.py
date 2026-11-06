from app.extensions import db
from app.models.activity import ActivityLog

def log_activity(project_id: int, stage: str, action: str, description: str, performed_by: str = "System", details: str = None):
    try:
        activity = ActivityLog(
            project_id=project_id,
            stage=stage,
            action=action,
            description=description,
            performed_by=performed_by,
            details=details
        )
        db.session.add(activity)
        db.session.commit()
        return activity
    except Exception as e:
        db.session.rollback()
        # Even if logging fails, don't crash main transaction
        return None

