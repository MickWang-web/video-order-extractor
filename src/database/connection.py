"""
数据库连接管理模块
"""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from src.core.config import DB_PATH

Base = declarative_base()
_engine = None
_SessionLocal = None


def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            echo=False,
            connect_args={"check_same_thread": False}
        )
    return _engine


def get_session() -> Session:
    """获取数据库会话"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def get_session_dependency() -> Generator[Session, None, None]:
    """FastAPI依赖注入用的session generator"""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """初始化数据库，创建所有表"""
    from src.models.order import Order
    from src.models.product import Product
    from src.models.order_product import OrderProduct
    from src.models.category import Category
    from src.models.import_log import ImportLog

    engine = get_engine()
    Base.metadata.create_all(engine)

    _init_default_categories()


def _init_default_categories():
    """初始化默认分类"""
    from src.dao.category_dao import CategoryDAO

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
                ("个人护理", 7, 2, 1),
                ("家居用品", 7, 2, 2),
                ("食品饮料", None, 1, 4),
                ("酒水饮料", 10, 2, 1),
                ("休闲零食", 10, 2, 2),
                ("米面粮油", 10, 2, 3),
                ("其他", None, 1, 99),
            ]
            for name, parent_id, level, sort_order in default_categories:
                CategoryDAO.create(session, {
                    "name": name,
                    "parent_id": parent_id,
                    "level": level,
                    "sort_order": sort_order
                })
    finally:
        session.close()


def close_engine():
    """关闭数据库引擎，释放资源"""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
