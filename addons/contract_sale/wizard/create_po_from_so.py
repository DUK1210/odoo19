from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CreatePoFromSoWizard(models.TransientModel):
    _name = 'create.po.from.so.wizard'
    _description = 'Tạo đơn mua hàng từ đơn bán'

    sale_order_id = fields.Many2one('sale.order', string='Đơn bán hàng', required=True,
                                     readonly=True)
    partner_id = fields.Many2one('res.partner', string='Nhà cung cấp', required=True,
                                   domain=[('supplier_rank', '>', 0)])
    line_ids = fields.One2many('create.po.from.so.wizard.line', 'wizard_id',
                                string='Chi tiết')

    @api.model
    def default_get(self, fields_list):
        res = super(CreatePoFromSoWizard, self).default_get(fields_list)
        sale_order_id = self.env.context.get('default_sale_order_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(sale_order_id)
            lines = []
            for so_line in sale_order.order_line:
                remaining = so_line.qty_remaining_to_purchase
                if remaining > 0:
                    lines.append((0, 0, {
                        'sale_order_line_id': so_line.id,
                        'product_id': so_line.product_id.id,
                        'qty_available': remaining,
                        'qty_to_purchase': remaining,
                    }))
            res['line_ids'] = lines
        return res

    def action_create_purchase_order(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Vui lòng thêm ít nhất một dòng sản phẩm!'))

        # Group lines by product
        po_lines = []
        for line in self.line_ids:
            if line.qty_to_purchase <= 0:
                continue
            po_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.qty_to_purchase,
                'sale_order_line_id': line.sale_order_line_id.id,
            }))

        if not po_lines:
            raise UserError(_('Vui lòng nhập số lượng cần mua!'))

        # Create PO
        po_vals = {
            'partner_id': self.partner_id.id,
            'sale_order_id': self.sale_order_id.id,
            'order_line': po_lines,
        }
        purchase_order = self.env['purchase.order'].create(po_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class CreatePoFromSoWizardLine(models.TransientModel):
    _name = 'create.po.from.so.wizard.line'
    _description = 'Dòng wizard tạo PO từ SO'

    wizard_id = fields.Many2one('create.po.from.so.wizard', string='Wizard',
                                 required=True, ondelete='cascade')
    sale_order_line_id = fields.Many2one('sale.order.line', string='Dòng SO',
                                          required=True, readonly=True)
    product_id = fields.Many2one('product.product', string='Sản phẩm',
                                  required=True, readonly=True)
    qty_available = fields.Float(string='SL còn lại', readonly=True,
                                  digits='Product Unit of Measure')
    qty_to_purchase = fields.Float(string='SL cần mua', required=True,
                                    digits='Product Unit of Measure')

    @api.constrains('qty_to_purchase')
    def _check_qty_to_purchase(self):
        for line in self:
            if line.qty_to_purchase < 0:
                raise UserError(_('Số lượng mua không được âm!'))
            if line.qty_to_purchase > line.qty_available:
                raise UserError(_(
                    'Không thể mua nhiều hơn số lượng còn lại cho %s!'
                ) % line.product_id.display_name)
