from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ContractSaleLine(models.Model):
    _name = 'contract.sale.line'
    _description = 'Chi tiết hợp đồng bán'

    contract_id = fields.Many2one('contract.sale', string='Hợp đồng', required=True,
                                   ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Sản phẩm', required=True,
                                    domain=[('sale_ok', '=', True)])
    qty_contract = fields.Float(string='SL hợp đồng', required=True,
                                 digits='Product Unit of Measure', default=1.0)
    price_unit = fields.Float(string='Đơn giá', required=True,
                               digits='Product Price', default=0.0)
    uom_id = fields.Many2one('uom.uom', string='Đơn vị tính', required=True)

    # Computed fields
    qty_sold = fields.Float(string='SL đã bán', compute='_compute_qty_sold',
                            store=True, digits='Product Unit of Measure')
    qty_remaining = fields.Float(string='Còn lại', compute='_compute_qty_remaining',
                                  store=True, digits='Product Unit of Measure')
    progress_percentage = fields.Float(string='Tiến độ %', compute='_compute_progress',
                                        store=True)

    qty_purchased = fields.Float(string='Đã mua', compute='_compute_qty_purchased',
                                  store=True, digits='Product Unit of Measure')
    qty_received = fields.Float(string='Đã nhận', compute='_compute_qty_received',
                                 store=True, digits='Product Unit of Measure')

    company_id = fields.Many2one('res.company', related='contract_id.company_id', store=True)
    currency_id = fields.Many2one('res.currency', related='contract_id.currency_id')
    subtotal = fields.Monetary(string='Thành tiền', compute='_compute_subtotal', store=True)

    _sql_constraints = [
        ('qty_positive', 'CHECK(qty_contract > 0)', 'Số lượng hợp đồng phải lớn hơn 0!'),
        ('price_positive', 'CHECK(price_unit >= 0)', 'Đơn giá không được âm!'),
    ]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.price_unit = self.product_id.lst_price

    @api.depends('qty_contract', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.qty_contract * line.price_unit

    @api.depends('contract_id.sale_order_ids.order_line',
                 'contract_id.sale_order_ids.state')
    def _compute_qty_sold(self):
        for line in self:
            domain = [
                ('order_id.contract_id', '=', line.contract_id.id),
                ('product_id', '=', line.product_id.id),
                ('state', 'in', ['sale', 'done']),
            ]
            sale_lines = self.env['sale.order.line'].search(domain)
            line.qty_sold = sum(sale_line.product_uom_qty for sale_line in sale_lines)

    @api.depends('qty_contract', 'qty_sold')
    def _compute_qty_remaining(self):
        for line in self:
            line.qty_remaining = line.qty_contract - line.qty_sold

    @api.depends('qty_contract', 'qty_sold')
    def _compute_progress(self):
        for line in self:
            if line.qty_contract > 0:
                line.progress_percentage = (line.qty_sold / line.qty_contract) * 100
            else:
                line.progress_percentage = 0.0

    @api.depends('contract_id.sale_order_ids.order_line',
                 'contract_id.sale_order_ids.purchase_order_ids.order_line')
    def _compute_qty_purchased(self):
        for line in self:
            qty = 0.0
            for so in line.contract_id.sale_order_ids:
                for po in so.purchase_order_ids:
                    if po.state in ['purchase', 'done']:
                        po_lines = po.order_line.filtered(
                            lambda l: l.product_id == line.product_id
                        )
                        qty += sum(l.product_qty for l in po_lines)
            line.qty_purchased = qty

    @api.depends('qty_purchased', 'contract_id.sale_order_ids.purchase_order_ids.picking_ids')
    def _compute_qty_received(self):
        for line in self:
            qty = 0.0
            for so in line.contract_id.sale_order_ids:
                for po in so.purchase_order_ids:
                    for picking in po.picking_ids:
                        if picking.state == 'done':
                            moves = picking.move_ids.filtered(
                                lambda m: m.product_id == line.product_id and
                                          m.state == 'done'
                            )
                            qty += sum(m.quantity for m in moves)
            line.qty_received = qty

    def get_progress_color(self):
        self.ensure_one()
        if self.progress_percentage >= 100:
            return 'danger'
        elif self.progress_percentage >= 80:
            return 'warning'
        return 'success'
