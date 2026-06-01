from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone

from app.utils.database import Base


class ImportLog(Base):
    __tablename__ = "import_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    import_type = Column(String(32), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    total_records = Column(Integer, default=0)
    new_records = Column(Integer, default=0)
    update_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    status = Column(String(32), nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}