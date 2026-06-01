from app.models.order_product import OrderProduct as OrderProductModel
from app.models.product import Product


class OrderProductDAO:

    @staticmethod
    def create(session, data: dict):
        op = OrderProductModel(**data)
        session.add(op)
        return op

    @staticmethod
    def delete_by_order(session, order_db_id: int) -> int:
        return session.query(OrderProductModel).filter(OrderProductModel.order_id == order_db_id).delete()

    @staticmethod
    def delete_all(session) -> int:
        return session.query(OrderProductModel).delete()

    @staticmethod
    def get_by_order(session, order_db_id: int) -> list:
        return session.query(OrderProductModel).filter(OrderProductModel.order_id == order_db_id).all()

    @staticmethod
    def get_products_for_order(session, order_db_id: int) -> list[dict]:
        results = session.query(OrderProductModel, Product).join(
            Product, OrderProductModel.product_id == Product.id
        ).filter(OrderProductModel.order_id == order_db_id).all()

        return [
            {
                "product_name": product.product_name,
                "quantity": op.quantity,
                "unit_price": op.unit_price,
                "subtotal": op.subtotal,
                "spec": op.spec or "",
            }
            for op, product in results
        ]

    @staticmethod
    def replace_by_order(session, order_db_id: int, products_data: list[dict]):
        OrderProductDAO.delete_by_order(session, order_db_id)
        from app.dao.product_dao import ProductDAO
        for product_data in products_data:
            OrderProductDAO.create(session, {
                "order_id": order_db_id,
                **product_data
            })