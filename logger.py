# Sports Schedulers - Activity Logger
# Author: Jose Ortiz
# Copyright: 2025

from models import db, ActivityLog
from flask import session
from datetime import datetime

def log_activity(user_id, action, entity_type, entity_id=None, details=None):
    """Log user activity to the database"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {e}")

def get_user_activities(user_id, limit=50):
    """Get recent activities for a user"""
    return ActivityLog.query.filter_by(user_id=user_id).order_by(
        ActivityLog.timestamp.desc()
    ).limit(limit).all()

def get_recent_activities(limit=100):
    """Get recent system activities"""
    return ActivityLog.query.order_by(
        ActivityLog.timestamp.desc()
    ).limit(limit).all()
