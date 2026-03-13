# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    filter_project_id = fields.Many2one(
        related='product_tmpl_id.filter_project_id',
        store=True,
        readonly=True,
    )
