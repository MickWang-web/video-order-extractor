import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from config import DB_PATH

Base = declarative_base()
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
    return _engine


def init_db():
    from app.models.order import Order
    from app.models.product import Product
    from app.models.order_product import OrderProduct
    from app.models.category import Category
    from app.models.import_log import ImportLog

    engine = get_engine()
    Base.metadata.create_all(engine)

    _init_default_categories()


def _init_default_categories():
    from app.dao.category_dao import CategoryDAO
    session = get_session()
    try:
        existing = CategoryDAO.get_all(session)
        if not existing:
            default_categories = [
                ("餐饮美食", None, 1, 1),
                ("外卖订餐", 1, 2, 1),
                ("到店餐饮", 1, 2, 2),
                ("生鲜水果", None, 1, 2),
                ("蔬菜水果", 4, 2, 1),
                ("肉禽蛋品", 4, 2, 2),
                ("日用百货", None, 1, 3),
                ("家居用品", 7, 2, 1),
                ("个人护理", 7, 2, 2),
                ("数码电子", None, 1, 4),
                ("服饰鞋包", None, 1, 5),
                ("其他", None, 1, 99),
            ]
            for name, parent_id, level, sort_order in default_categories:
                CategoryDAO.create(session, {
                    "name": name,
                    "parent_id": parent_id,
                    "level": level,
                    "sort_order": sort_order
                })
            session.commit()
    finally:
        session.close()


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()


def close_engine():
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None