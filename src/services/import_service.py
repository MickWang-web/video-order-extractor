from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.dao.order_dao import OrderDAO
from src.dao.order_product_dao import OrderProductDAO
from src.dao.product_dao import ProductDAO
from src.dao.import_log_dao import ImportLogDAO


def _parse_datetime(dt_val):
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y.%m.%d',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_val, fmt)
        except (ValueError, TypeError):
            continue
    return None


class ImportService:

    @staticmethod
    def import_orders(session: Session, orders_data: list[dict], source_type: str, source_name: str) -> dict:
        stats = {
            "total_records": len(orders_data),
            "new_records": 0,
            "update_records": 0,
            "duplicate_records": 0,
            "failed_records": 0,
            "error_messages": []
        }

        for order_data in orders_data:
            try:
                order_id = str(order_data.get("order_id", "")).strip()
                if not order_id or len(order_id) < 10:
                    stats["failed_records"] += 1
                    stats["error_messages"].append(f"无效订单号: {order_id}")
                    continue

                existing = OrderDAO.get_by_order_id(session, order_id)
                products_data = order_data.pop("products", []) if "products" in order_data else []

                if "datetime" in order_data:
                    order_data["datetime"] = _parse_datetime(order_data["datetime"])

                if existing:
                    OrderDAO.update(session, order_id, order_data)
                    stats["update_records"] += 1

                    if products_data:
                        OrderProductDAO.delete_by_order(session, existing.id)
                        _link_products(session, existing.id, products_data)
                else:
                    new_order = OrderDAO.create(session, order_data)
                    stats["new_records"] += 1

                    if products_data:
                        _link_products(session, new_order.id, products_data)

            except Exception as e:
                stats["failed_records"] += 1
                stats["error_messages"].append(f"处理订单失败: {str(e)}")

        ImportLogDAO.create(session, {
            "import_type": source_type,
            "source_name": source_name,
            "total_records": stats["total_records"],
            "new_records": stats["new_records"],
            "update_records": stats["update_records"],
            "duplicate_records": stats["duplicate_records"],
            "status": "success" if stats["failed_records"] == 0 else "partial",
            "error_message": "\n".join(stats["error_messages"]) if stats["error_messages"] else None
        })

        return stats

    @staticmethod
    def get_all_orders(session: Session) -> list[dict]:
        orders = OrderDAO.get_all(session)
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict["products"] = OrderProductDAO.get_products_for_order(session, order.id)
            result.append(order_dict)
        return result

    @staticmethod
    def get_orders_by_date_range(session: Session, start: datetime, end: datetime) -> list[dict]:
        orders = OrderDAO.get_by_time_range(session, start, end)
        result = []
        for order in orders:
            order_dict = order.to_dict()
            order_dict["products"] = OrderProductDAO.get_products_for_order(session, order.id)
            result.append(order_dict)
        return result

    @staticmethod
    def get_summary(session: Session, start: datetime = None, end: datetime = None) -> dict:
        return OrderDAO.get_summary(session, start, end)

    @staticmethod
    def delete_order(session: Session, order_id: str) -> bool:
        order = OrderDAO.get_by_order_id(session, order_id)
        if not order:
            return False
        OrderProductDAO.delete_by_order(session, order.id)
        OrderDAO.delete(session, order_id)
        session.commit()
        return True

    @staticmethod
    def import_orders_full_refresh(session: Session, orders_data: list[dict], source_type: str, source_name: str) -> dict:
        OrderDAO.delete_all(session)
        OrderProductDAO.delete_all(session)
        return ImportService.import_orders(session, orders_data, source_type, source_name)


def _link_products(session: Session, db_order_id: int, products_data: list[dict]):
    for product_data in products_data:
        product_name = product_data.get("product_name", "").strip()
        if not product_name:
            continue

        product = ProductDAO.find_or_create(session, product_name)

        quantity = int(product_data.get("quantity", 1))
        unit_price = float(product_data.get("unit_price", 0.0))
        subtotal = float(product_data.get("subtotal", 0.0))
        spec = product_data.get("spec", "")

        OrderProductDAO.create(session, {
            "order_id": db_order_id,
            "product_id": product.id,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "spec": spec
        })