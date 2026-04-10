from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_order_id = fields.Many2one('sale.order', string='Source Sale Order',
                                     compute='_compute_sale_order_id', store=True,
                                     index=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order',
                                          related='purchase_id', store=True)

    @api.depends('purchase_id', 'purchase_id.sale_order_id')
    def _compute_sale_order_id(self):
        for picking in self:
            if picking.purchase_id and picking.purchase_id.sale_order_id:
                picking.sale_order_id = picking.purchase_id.sale_order_id.id
            else:
                picking.sale_order_id = False

    def button_validate(self):
        # Validate receipt quantity doesn't exceed PO
        for picking in self:
            if picking.purchase_id:
                precision = self.env['decimal.precision'].precision_get(
                    'Product Unit of Measure'
                )
                for move in picking.move_ids:
                    if move.purchase_line_id and move.purchase_line_id.sale_order_line_id:
                        so_line = move.purchase_line_id.sale_order_line_id
                        # Check if receiving more than SO quantity
                        qty_done = move.quantity
                        already_received = so_line.qty_received
                        so_qty = so_line.product_uom_qty

                        if float_compare(
                            already_received + qty_done,
                            so_qty,
                            precision_digits=precision
                        ) > 0:
                            raise UserError(_(
                                'Cannot receive more than Sale Order quantity for %(product)s!\n'
                                'SO Quantity: %(so_qty)s\n'
                                'Already Received: %(received)s\n'
                                'Current: %(current)s'
                            ) % {
                                'product': move.product_id.display_name,
                                'so_qty': so_qty,
                                'received': already_received,
                                'current': qty_done,
                            })

        return super(StockPicking, self).button_validate()

    def action_view_sale_order(self):
        self.ensure_one()
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'view_mode': 'form',
            }
        return False

    def action_view_contract(self):
        self.ensure_one()
        if self.sale_order_id and self.sale_order_id.contract_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'contract.sale',
                'res_id': self.sale_order_id.contract_id.id,
                'view_mode': 'form',
            }
        return False
