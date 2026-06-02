from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.product import Product
from src.models.order_product import OrderProduct


class ProductDAO:

    @staticmethod
    def get_by_id(session: Session, product_id: int) -> Product | None:
        return session.get(Product, product_id)

    @staticmethod
    def get_by_name(session: Session, product_name: str) -> Product | None:
        return session.query(Product).filter(Product.product_name == product_name).first()

    @staticmethod
    def search_by_name(session: Session, keyword: str) -> list[Product]:
        return session.query(Product).filter(Product.product_name.contains(keyword)).all()

    @staticmethod
    def get_by_category(session: Session, category_id: int) -> list[Product]:
        return session.query(Product).filter(Product.category_id == category_id).all()

    @staticmethod
    def get_all(session: Session) -> list[Product]:
        return session.query(Product).all()

    @staticmethod
    def create(session: Session, product_data: dict) -> Product:
        product = Product(**product_data)
        session.add(product)
        session.flush()
        return product

    @staticmethod
    def find_or_create(session: Session, product_name: str, default_data: dict = None) -> Product:
        existing = ProductDAO.get_by_name(session, product_name)
        if existing:
            return existing
        data = {"product_name": product_name}
        if default_data:
            data.update(default_data)
        return ProductDAO.create(session, data)

    @staticmethod
    def update(session: Session, product_id: int, data: dict) -> int:
        return session.query(Product).filter(Product.id == product_id).update(data)

    @staticmethod
    def get_sales_ranking(session: Session, limit: int = 10) -> list[dict]:
        results = session.query(
            Product.product_name,
            func.sum(OrderProduct.quantity).label("total_quantity"),
            func.sum(OrderProduct.subtotal).label("total_sales")
        ).join(OrderProduct, Product.id == OrderProduct.product_id)\
            .group_by(Product.id)\
            .order_by(func.sum(OrderProduct.subtotal).desc())\
            .limit(limit)\
            .all()

        return [
            {
                "product_name": name,
                "total_quantity": int(qty or 0),
                "total_sales": round(float(sales or 0), 2)
            }
            for name, qty, sales in results
        ]