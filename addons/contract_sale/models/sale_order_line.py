from odoo import api, fields, models, _
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    contract_line_id = fields.Many2one('contract.sale.line', string='Dòng hợp đồng',
                                        compute='_compute_contract_line_id', store=True)
    purchase_line_ids = fields.One2many('purchase.order.line', 'sale_order_line_id',
                                         string='Dòng đơn mua')
    qty_purchased = fields.Float(string='Đã mua', compute='_compute_qty_purchased',
                                  store=True, digits='Product Unit of Measure')
    qty_remaining_to_purchase = fields.Float(string='Còn lại chưa mua',
                                              compute='_compute_qty_remaining_to_purchase',
                                              store=True, digits='Product Unit of Measure')
    qty_received = fields.Float(string='Đã nhận', compute='_compute_qty_received',
                                 store=True, digits='Product Unit of Measure')

    @api.depends('order_id.contract_id', 'product_id')
    def _compute_contract_line_id(self):
        for line in self:
            if line.order_id.contract_id and line.product_id:
                contract_line = line.order_id.contract_id.line_ids.filtered(
                    lambda l: l.product_id == line.product_id
                )
                line.contract_line_id = contract_line[0] if contract_line else False
            else:
                line.contract_line_id = False

    @api.depends('purchase_line_ids', 'purchase_line_ids.state')
    def _compute_qty_purchased(self):
        for line in self:
            qty = 0.0
            for po_line in line.purchase_line_ids:
                if po_line.state in ['purchase', 'done']:
                    qty += po_line.product_qty
            line.qty_purchased = qty

    @api.depends('product_uom_qty', 'qty_purchased')
    def _compute_qty_remaining_to_purchase(self):
        for line in self:
            line.qty_remaining_to_purchase = line.product_uom_qty - line.qty_purchased

    @api.depends('purchase_line_ids.move_ids', 'purchase_line_ids.move_ids.state')
    def _compute_qty_received(self):
        for line in self:
            qty = 0.0
            for po_line in line.purchase_line_ids:
                for move in po_line.move_ids:
                    if move.state == 'done':
                        qty += move.quantity
            line.qty_received = qty

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_contract(self):
        if self.order_id.contract_id and self.product_id:
            contract_line = self.order_id.contract_id.line_ids.filtered(
                lambda l: l.product_id == self.product_id
            )
            if contract_line:
                remaining = contract_line[0].qty_remaining
                precision = self.env['decimal.precision'].precision_get(
                    'Product Unit of Measure'
                )
                if float_compare(self.product_uom_qty, remaining, precision_digits=precision) > 0:
                    return {
                        'warning': {
                            'title': _('Quantity Warning'),
                            'message': _(
                                'Quantity exceeds contract remaining limit!\n'
                                'Requested: %(requested)s\n'
                                'Available: %(available)s'
                            ) % {
                                'requested': self.product_uom_qty,
                                'available': remaining,
                            }
                        }
                    }
