from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_id = fields.Many2one('sale.order', string='Source Sale Order',
                                       domain=[('state', 'in', ['sale', 'done'])],
                                       tracking=True, index=True)

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            # Auto-fill order lines from SO
            if not self.order_line:
                lines = []
                for so_line in self.sale_order_id.order_line:
                    remaining = so_line.qty_remaining_to_purchase
                    if remaining > 0:
                        lines.append((0, 0, {
                            'product_id': so_line.product_id.id,
                            'product_qty': remaining,
                            'price_unit': 0.0,  # Will be updated by onchange
                            'sale_order_line_id': so_line.id,
                        }))
                self.order_line = lines

    def _validate_so_quantities(self):
        """Validate that PO quantities don't exceed SO limits."""
        self.ensure_one()
        if not self.sale_order_id:
            return

        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure'
        )

        for line in self.order_line:
            if line.sale_order_line_id:
                remaining = line.sale_order_line_id.qty_remaining_to_purchase
                if float_compare(line.product_qty, remaining, precision_digits=precision) > 0:
                    raise UserError(_(
                        'Quantity for %(product)s exceeds SO remaining limit!\n'
                        'Requested: %(requested)s\n'
                        'Available: %(available)s'
                    ) % {
                        'product': line.product_id.display_name,
                        'requested': line.product_qty,
                        'available': remaining,
                    })

    def button_confirm(self):
        for order in self:
            if order.sale_order_id:
                # Validate SO is confirmed
                if order.sale_order_id.state not in ['sale', 'done']:
                    raise UserError(_(
                        'Source Sale Order %s is not confirmed!'
                    ) % order.sale_order_id.name)
                # Validate quantities
                order._validate_so_quantities()

        return super(PurchaseOrder, self).button_confirm()

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        # Rollback will be handled by computed fields
        return res

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
