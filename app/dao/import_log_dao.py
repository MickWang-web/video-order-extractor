from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.import_log import ImportLog


class ImportLogDAO:

    @staticmethod
    def create(session: Session, log_data: dict) -> ImportLog:
        log = ImportLog(**log_data)
        session.add(log)
        return log

    @staticmethod
    def get_by_time_range(session: Session, start: datetime, end: datetime) -> list[ImportLog]:
        return session.query(ImportLog).filter(
            ImportLog.created_at >= start,
            ImportLog.created_at <= end
        ).order_by(ImportLog.created_at.desc()).all()

    @staticmethod
    def get_by_type(session: Session, import_type: str) -> list[ImportLog]:
        return session.query(ImportLog).filter(ImportLog.import_type == import_type).order_by(ImportLog.created_at.desc()).all()

    @staticmethod
    def get_all(session: Session) -> list[ImportLog]:
        return session.query(ImportLog).order_by(ImportLog.created_at.desc()).all()

    @staticmethod
    def get_summary(session: Session) -> dict:
        total = session.query(func.count(ImportLog.id)).scalar()
        success = session.query(func.count(ImportLog.id)).filter(ImportLog.status == "success").scalar()
        failed = session.query(func.count(ImportLog.id)).filter(ImportLog.status != "success").scalar()
        total_new = session.query(func.sum(ImportLog.new_records)).scalar() or 0
        total_update = session.query(func.sum(ImportLog.update_records)).scalar() or 0

        return {
            "total_imports": total,
            "success_imports": success,
            "failed_imports": failed,
            "total_new_records": int(total_new),
            "total_update_records": int(total_update),
        }