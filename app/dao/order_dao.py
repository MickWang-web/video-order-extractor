from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order


class OrderDAO:

    @staticmethod
    def get_by_id(session: Session, pk: int) -> Order | None:
        return session.get(Order, pk)

    @staticmethod
    def get_by_order_id(session: Session, order_id: str) -> Order | None:
        return session.query(Order).filter(Order.order_id == order_id).first()

    @staticmethod
    def get_all(session: Session) -> list[Order]:
        return session.query(Order).order_by(Order.datetime.desc()).all()

    @staticmethod
    def get_by_time_range(session: Session, start: datetime, end: datetime) -> list[Order]:
        return session.query(Order).filter(
            Order.datetime >= start,
            Order.datetime <= end
        ).order_by(Order.datetime.desc()).all()

    @staticmethod
    def get_by_status(session: Session, status: str) -> list[Order]:
        return session.query(Order).filter(Order.status == status).order_by(Order.datetime.desc()).all()

    @staticmethod
    def create(session: Session, order_data: dict) -> Order:
        order = Order(**order_data)
        session.add(order)
        session.flush()
        return order

    @staticmethod
    def update(session: Session, order_id: str, data: dict) -> int:
        return session.query(Order).filter(Order.order_id == order_id).update(data)

    @staticmethod
    def upsert(session: Session, order_data: dict) -> Order:
        existing = session.query(Order).filter(Order.order_id == order_data["order_id"]).first()
        if existing:
            for key, value in order_data.items():
                if key != "order_id":
                    setattr(existing, key, value)
            return existing
        else:
            return OrderDAO.create(session, order_data)

    @staticmethod
    def delete(session: Session, order_id: str) -> int:
        return session.query(Order).filter(Order.order_id == order_id).delete()

    @staticmethod
    def delete_all(session: Session) -> int:
        return session.query(Order).delete()

    @staticmethod
    def get_count(session: Session) -> int:
        return session.query(func.count(Order.id)).scalar()

    @staticmethod
    def get_summary(session: Session, start: datetime = None, end: datetime = None) -> dict:
        query = session.query(Order)
        if start:
            query = query.filter(Order.datetime >= start)
        if end:
            query = query.filter(Order.datetime <= end)

        completed = query.filter(Order.status == "已完成").all()
        refunded = query.filter(Order.status == "已退款").all()
        all_orders = query.all()

        completed_amount = sum(o.amount for o in completed)
        refund_amount = sum(o.amount for o in refunded)
        qyk_count = sum(1 for o in all_orders if o.tags and "亲友卡" in o.tags)
        qyk_amount = sum(o.amount for o in all_orders if o.tags and "亲友卡" in o.tags and o.status == "已完成")

        return {
            "total_orders": len(all_orders),
            "completed_count": len(completed),
            "refund_count": len(refunded),
            "completed_amount": round(completed_amount, 2),
            "refund_amount": round(refund_amount, 2),
            "net_amount": round(completed_amount + refund_amount, 2),
            "qyk_count": qyk_count,
            "qyk_completed_amount": round(qyk_amount, 2),
        }