from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryDAO:

    @staticmethod
    def get_by_id(session: Session, category_id: int) -> Category | None:
        return session.get(Category, category_id)

    @staticmethod
    def get_by_name(session: Session, name: str) -> Category | None:
        return session.query(Category).filter(Category.name == name).first()

    @staticmethod
    def get_all(session: Session) -> list[Category]:
        return session.query(Category).order_by(Category.sort_order).all()

    @staticmethod
    def get_roots(session: Session) -> list[Category]:
        return session.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.sort_order).all()

    @staticmethod
    def get_children(session: Session, parent_id: int) -> list[Category]:
        return session.query(Category).filter(Category.parent_id == parent_id).order_by(Category.sort_order).all()

    @staticmethod
    def create(session: Session, category_data: dict) -> Category:
        category = Category(**category_data)
        session.add(category)
        return category

    @staticmethod
    def update(session: Session, category_id: int, data: dict) -> int:
        return session.query(Category).filter(Category.id == category_id).update(data)