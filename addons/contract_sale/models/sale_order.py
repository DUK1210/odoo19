from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('contract.sale', string='Contract',
                                   domain=[('state', '=', 'active')],
                                   tracking=True, index=True)

    # Purchase tracking fields
    purchase_order_ids = fields.One2many('purchase.order', 'sale_order_id',
                                          string='Purchase Orders')
    purchase_order_count = fields.Integer(string='PO Count',
                                           compute='_compute_purchase_order_count')

    qty_purchased = fields.Float(string='Purchased Qty', compute='_compute_qty_purchased',
                                  digits='Product Unit of Measure', store=True)
    qty_remaining_to_purchase = fields.Float(string='Remaining to Purchase',
                                              compute='_compute_qty_remaining_to_purchase',
                                              digits='Product Unit of Measure', store=True)
    qty_received = fields.Float(string='Received Qty', compute='_compute_qty_received',
                                 digits='Product Unit of Measure', store=True)

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for order in self:
            order.purchase_order_count = len(order.purchase_order_ids)

    @api.depends('order_line.qty_purchased')
    def _compute_qty_purchased(self):
        for order in self:
            order.qty_purchased = sum(line.qty_purchased for line in order.order_line)

    @api.depends('order_line.product_uom_qty', 'order_line.qty_purchased')
    def _compute_qty_remaining_to_purchase(self):
        for order in self:
            order.qty_remaining_to_purchase = sum(
                line.product_uom_qty - line.qty_purchased for line in order.order_line
            )

    @api.depends('order_line.qty_received')
    def _compute_qty_received(self):
        for order in self:
            order.qty_received = sum(line.qty_received for line in order.order_line)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Filter contracts by partner
            return {'domain': {'contract_id': [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'active')
            ]}}
        return {'domain': {'contract_id': [('state', '=', 'active')]}}

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            # Validate contract state
            if self.contract_id.state != 'active':
                return {
                    'warning': {
                        'title': _('Invalid Contract'),
                        'message': _('Selected contract is not active!')
                    }
                }
            if self.contract_id.partner_id != self.partner_id:
                return {
                    'warning': {
                        'title': _('Contract Mismatch'),
                        'message': _('Contract customer does not match order customer!')
                    }
                }

    @api.constrains('contract_id', 'partner_id')
    def _check_contract_partner(self):
        for order in self:
            if order.contract_id and order.contract_id.partner_id != order.partner_id:
                raise ValidationError(_('Contract customer must match order customer!'))

    def _validate_contract_quantities(self):
        """Validate that SO quantities don't exceed contract limits."""
        self.ensure_one()
        if not self.contract_id:
            return

        for line in self.order_line:
            # Find matching contract line
            contract_line = self.contract_id.line_ids.filtered(
                lambda l: l.product_id == line.product_id
            )
            if not contract_line:
                raise UserError(_(
                    'Product %s is not in the contract!'
                ) % line.product_id.display_name)

            contract_line = contract_line[0]
            # Check quantity
            remaining = contract_line.qty_remaining
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure'
            )
            if float_compare(line.product_uom_qty, remaining, precision_digits=precision) > 0:
                raise UserError(_(
                    'Quantity for %(product)s exceeds contract limit!\n'
                    'Requested: %(requested)s\n'
                    'Remaining: %(remaining)s'
                ) % {
                    'product': line.product_id.display_name,
                    'requested': line.product_uom_qty,
                    'remaining': remaining,
                })

    def _update_contract_qty_sold(self):
        """Update qty_sold on contract lines after SO confirmation."""
        self.ensure_one()
        if not self.contract_id:
            return
        # The computed fields on contract.sale.line will auto-update
        # due to @api.depends on sale order state
        pass

    def _rollback_contract_qty_sold(self):
        """Rollback qty_sold when SO is cancelled."""
        self.ensure_one()
        if not self.contract_id:
            return
        # The computed fields will auto-update when state changes
        pass

    def action_confirm(self):
        for order in self:
            if order.contract_id:
                # Check contract is active
                if order.contract_id.state != 'active':
                    raise UserError(_(
                        'Cannot confirm order. Contract %s is not active!'
                    ) % order.contract_id.name)
                # Validate quantities
                order._validate_contract_quantities()

        res = super(SaleOrder, self).action_confirm()

        # Update contract after confirmation
        for order in self:
            if order.contract_id:
                order._update_contract_qty_sold()

        return res

    def _action_cancel(self):
        res = super(SaleOrder, self)._action_cancel()
        for order in self:
            if order.contract_id:
                order._rollback_contract_qty_sold()
        return res

    def action_create_purchase_order(self):
        """Open wizard to create PO from SO."""
        self.ensure_one()
        return {
            'name': _('Create Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.po.from.so.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'purchase.purchase_form_action'
        )
        action['domain'] = [('sale_order_id', '=', self.id)]
        return action

    def action_view_receipts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'stock.action_picking_tree_all'
        )
        picking_ids = []
        for po in self.purchase_order_ids:
            picking_ids.extend(po.picking_ids.ids)
        action['domain'] = [('id', 'in', picking_ids)]
        return action
