"""
Módulo de Servicios de Negocio - Farmacia POS
Contiene autenticación, inventario FEFO, ventas multi-sucursal y analítica con KPIs y gráficos.
"""
from .auth_service import (
    hash_password,
    verify_password,
    login,
    logout,
    get_current_user,
    get_current_branch,
    get_current_branch_id,
    set_current_branch,
    create_user,
    list_users,
    toggle_user_status,
    list_roles
)
from .inventory_service import (
    list_branches,
    create_branch,
    search_products,
    get_product_by_barcode,
    get_product_by_id,
    get_product_fefo_batches,
    validate_stock_fefo,
    deduct_stock_fefo,
    check_batch_expirations,
    create_product,
    create_batch,
    get_all_products_with_stock,
    get_inventory_statistics
)
from .sales_service import (
    CartItem,
    ShoppingCart,
    process_sale,
    get_sales_history,
    get_sale_details,
    get_sales_summary_today
)
from .analytics_service import (
    get_kpis_and_metrics,
    get_temporal_sales_trend,
    get_top_selling_products,
    get_payment_methods_distribution,
    get_sales_by_branch_comparison
)

__all__ = [
    "hash_password",
    "verify_password",
    "login",
    "logout",
    "get_current_user",
    "get_current_branch",
    "get_current_branch_id",
    "set_current_branch",
    "create_user",
    "list_users",
    "toggle_user_status",
    "list_roles",
    "list_branches",
    "create_branch",
    "search_products",
    "get_product_by_barcode",
    "get_product_by_id",
    "get_product_fefo_batches",
    "validate_stock_fefo",
    "deduct_stock_fefo",
    "check_batch_expirations",
    "create_product",
    "create_batch",
    "get_all_products_with_stock",
    "get_inventory_statistics",
    "CartItem",
    "ShoppingCart",
    "process_sale",
    "get_sales_history",
    "get_sale_details",
    "get_sales_summary_today",
    "get_kpis_and_metrics",
    "get_temporal_sales_trend",
    "get_top_selling_products",
    "get_payment_methods_distribution",
    "get_sales_by_branch_comparison"
]
