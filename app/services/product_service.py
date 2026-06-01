from sqlalchemy.orm import Session
from app.dao.product_dao import ProductDAO
from app.dao.order_product_dao import OrderProductDAO
from app.models.product import Product


class ProductService:

    @staticmethod
    def match_or_create_product(session: Session, product_name: str, default_data: dict = None) -> Product:
        exact = ProductDAO.get_by_name(session, product_name)
        if exact:
            return exact

        similar = ProductDAO.search_by_name(session, product_name)
        for product in similar:
            similarity = _calculate_similarity(product.product_name, product_name)
            if similarity > 0.8:
                return product

        return ProductDAO.find_or_create(session, product_name, default_data)

    @staticmethod
    def get_product_statistics(session: Session, category_id: int = None) -> list[dict]:
        return ProductDAO.get_sales_ranking(session)

    @staticmethod
    def assign_category(session: Session, product_id: int, category_id: int) -> bool:
        result = ProductDAO.update(session, product_id, {"category_id": category_id})
        return result > 0


def _calculate_similarity(str1: str, str2: str) -> float:
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0
    matches = sum(1 for a, b in zip(str1, str2) if a == b)
    return matches / max_len