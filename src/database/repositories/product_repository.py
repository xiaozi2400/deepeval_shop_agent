"""商品数据访问层"""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from src.database.models import Product


class SQLiteProductRepository:
    """基于 SQLite 的商品仓库"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_sku(self, sku_id: str) -> Product | None:
        """按 sku_id 精确查询，忽略大小写"""
        if not sku_id:
            return None
        stmt = select(Product).where(Product.sku_id.ilike(sku_id))
        return self.session.execute(stmt).scalars().first()

    def find_by_name(self, name: str) -> list[Product]:
        """按商品名模糊查询，完全相等的命中排在前面"""
        if not name:
            return []

        exact = list(
            self.session.execute(
                select(Product).where(Product.name == name)
            ).scalars().all()
        )
        if exact:
            return exact

        stmt = select(Product).where(
            or_(
                Product.name.ilike(f"%{name}%"),
                Product.sku_id.ilike(f"%{name}%"),
            )
        )
        return list(self.session.execute(stmt).scalars().all())

    def resolve(self, keyword: str) -> Product | None:
        """把用户给的商品名或 SKU 解析成商品

        依次尝试：SKU 精确命中 → 商品名精确命中 → 商品名/SKU 模糊命中 →
        商品名出现在传入文本里（LLM 常把整句问法一起塞进参数）。
        """
        text = (keyword or "").strip()
        if not text:
            return None

        product = self.get_by_sku(text)
        if product is not None:
            return product

        matches = self.find_by_name(text)
        if matches:
            return matches[0]

        return self._find_contained_in(text)

    def _find_contained_in(self, text: str) -> Product | None:
        """传入文本里含有某个商品名时命中该商品，取名字最长的那个"""
        lowered = text.lower()
        candidates = [
            product
            for product in self.session.execute(select(Product)).scalars().all()
            if product.name and product.name.lower() in lowered
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda product: len(product.name))
