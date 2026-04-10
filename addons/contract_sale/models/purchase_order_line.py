from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sale_order_line_id = fields.Many2one('sale.order.line', string='Source SO Line',
                                          index=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Suggest quantity from remaining SO qty
        if self.sale_order_line_id and self.product_id:
            self.product_qty = self.sale_order_line_id.qty_remaining_to_purchase
