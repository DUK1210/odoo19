{
    "name": "Quản lý hợp đồng bán",
    "version": "1.0.0",
    "category": "Sales/Contracts",
    "summary": "Quản lý thầu - Contract → SO → PO → Receipt",
    "description": """
        Module quản lý toàn bộ luồng nghiệp vụ:
        Contract → Sale Order → Purchase Order → Stock Receipt
        
        Tính năng:
        - Không cho vượt số lượng ở bất kỳ bước nào
        - Dữ liệu truy vết xuyên suốt
        - Dashboard và báo cáo realtime
        - Hệ thống cảnh báo tự động
    """,
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "sale_management",
        "purchase",
        "stock",
        "mail",
        "web",
    ],
    "data": [
        "security/contract_sale_security.xml",
        "security/ir.model.access.csv",
        "data/contract_sale_cron.xml",
        "data/mail_template.xml",
        "views/contract_sale_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        # "views/contract_sale_dashboard_views.xml",
        "wizard/create_po_from_so_views.xml",
        "views/report_contract_sale.xml",
        # "report/contract_sale_report_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
    "assets": {
        "web.assets_backend": [
            "contract_sale/static/src/css/contract_sale.css",
            "contract_sale/static/src/js/contract_sale_dashboard.js",
        ],
    },
}
