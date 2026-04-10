from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Source SO Line',
                                          related='purchase_line_id.sale_order_line_id',
                                          store=True, index=True)
    contract_id = fields.Many2one('contract.sale', string='Contract',
                                   related='sale_order_line_id.order_id.contract_id',
                                   store=True, index=True)
