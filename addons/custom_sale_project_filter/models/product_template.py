# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    filter_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Dự án',
        ondelete='set null',
        index=True,
        help='Gắn sản phẩm này với một dự án cụ thể. '
             'Khi bán hàng có chọn dự án, chỉ các sản phẩm thuộc '
             'dự án đó mới được hiển thị trong order line.',
    )
