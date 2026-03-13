# -*- coding: utf-8 -*-
{
    'name': 'Custom Sale Project Filter',
    'version': '19.0.1.0.0',
    'summary': 'Lọc sản phẩm theo dự án trên Sale Order (Custom)',
    'description': """
        Cho phép gắn dự án (project.project) vào sản phẩm (product.template).
        Khi chọn dự án trên Sale Order, danh sách sản phẩm trên Order Line
        sẽ tự động lọc theo dự án đã chọn.
    """,
    'category': 'Sales/Sales',
    'author': 'Custom Dev',
    'depends': [
        'sale_management',
        'project',
        'sale_project',
    ],
    'data': [
        'views/product_template_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
