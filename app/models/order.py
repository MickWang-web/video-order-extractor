from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime, timezone

from app.utils.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False)
    datetime = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    tags = Column(Text, nullable=True)
    platform = Column(String(32), nullable=True)
    location = Column(String(64), nullable=True, index=True)
    member_card = Column(String(32), nullable=True)
    subtotal = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    rebate = Column(Float, nullable=True)
    tax_excluded = Column(Float, nullable=True)
    actual_pay = Column(Float, nullable=True)
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}