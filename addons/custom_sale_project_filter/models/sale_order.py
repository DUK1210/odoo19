# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('project_id')
    def _onchange_project_id_filter_lines(self):
        """Khi đổi dự án, xóa các dòng order line có sản phẩm không thuộc dự án mới."""
        if self.project_id:
            invalid_lines = self.order_line.filtered(
                lambda l: l.product_id
                and l.product_id.product_tmpl_id.filter_project_id
                and l.product_id.product_tmpl_id.filter_project_id != self.project_id
            )
            if invalid_lines:
                invalid_lines.unlink()
