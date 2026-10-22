from app.tools.cart_tools import TOOL_HANDLERS as _cart_handlers
from app.tools.order_tools import TOOL_HANDLERS as _order_handlers
from app.tools.product_tools import TOOL_HANDLERS as _product_handlers

ALL_HANDLERS: dict = {**_product_handlers, **_cart_handlers, **_order_handlers}
