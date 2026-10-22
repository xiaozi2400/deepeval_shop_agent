"""商品查询工具"""
from langchain_core.tools import tool

from src.database.connection import get_session
from src.database.repositories.product_repository import SQLiteProductRepository
from src.schemas import ProductResult


@tool
def query_product(sku_id: str) -> ProductResult:
    """查询商品的售价与库存。

    Args:
        sku_id: 商品 SKU 编号或商品名称，例如 "SKU-IPHONE-15-PROMAX-256"
            或 "iPhone 15 Pro Max 256GB"。名称会被解析成对应的 SKU。

    Returns:
        商品的价格、库存与分类；缺参数时 needs_input 为 True，商品不存在时 found 为 False。
    """
    keyword = (sku_id or "").strip()
    if not keyword:
        return ProductResult(
            found=False,
            needs_input=True,
            message="需要商品信息才能查询。请让用户提供商品名称或 SKU 编号，"
                    "例如「iPhone 15 Pro Max 256GB」或「SKU-IPHONE-15-PROMAX-256」。",
        )

    with get_session() as session:
        repo = SQLiteProductRepository(session)
        product = repo.resolve(keyword)

        if product is None:
            return ProductResult(
                found=False,
                message=f"未找到与「{keyword}」匹配的商品。可以请用户提供更完整的商品名称，"
                        f"或换个说法描述想买的东西。",
            )

        in_stock = product.stock > 0
        return ProductResult(
            found=True,
            sku_id=product.sku_id,
            name=product.name,
            price=product.price,
            stock=product.stock,
            in_stock=in_stock,
            category=product.category or "",
        )
