from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ContractSale(models.Model):
    _name = 'contract.sale'
    _description = 'Hợp đồng bán hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'

    name = fields.Char(string='Số hợp đồng', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Khách hàng', required=True,
                                  tracking=True, index=True)
    date_start = fields.Date(string='Ngày bắt đầu', required=True, tracking=True)
    date_end = fields.Date(string='Ngày kết thúc', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('active', 'Đang hoạt động'),
        ('expired', 'Hết hạn'),
        ('done', 'Hoàn thành'),
    ], string='Trạng thái', default='draft', tracking=True, index=True)

    line_ids = fields.One2many('contract.sale.line', 'contract_id',
                                string='Chi tiết hợp đồng')

    # Computed fields
    qty_sold = fields.Float(string='Tổng đã bán', compute='_compute_qty_sold',
                            store=True, digits='Product Unit of Measure')
    qty_remaining = fields.Float(string='Còn lại', compute='_compute_qty_remaining',
                                  store=True, digits='Product Unit of Measure')
    progress_percentage = fields.Float(string='Tiến độ %', compute='_compute_progress',
                                        store=True)

    sale_order_count = fields.Integer(string='Số đơn bán', compute='_compute_sale_order_count')
    sale_order_ids = fields.One2many('sale.order', 'contract_id', string='Đơn bán hàng')

    alert_sent = fields.Boolean(string='Đã gửi cảnh báo', default=False,
                                 help='Đánh dấu nếu đã gửi cảnh báo số lượng thấp')
    expiry_alert_sent = fields.Boolean(string='Đã gửi cảnh báo hết hạn', default=False)

    company_id = fields.Many2one('res.company', string='Công ty',
                                  default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ',
                                     related='company_id.currency_id', store=True)
    total_amount = fields.Monetary(string='Tổng giá trị', compute='_compute_total_amount',
                                    store=True)

    _sql_constraints = [
        ('date_check', 'CHECK(date_end >= date_start)',
         'Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu!'),
    ]

    @api.depends('line_ids.qty_contract', 'line_ids.price_unit')
    def _compute_total_amount(self):
        for contract in self:
            contract.total_amount = sum(
                line.qty_contract * line.price_unit for line in contract.line_ids
            )

    @api.depends('line_ids.qty_sold')
    def _compute_qty_sold(self):
        for contract in self:
            contract.qty_sold = sum(line.qty_sold for line in contract.line_ids)

    @api.depends('line_ids.qty_remaining')
    def _compute_qty_remaining(self):
        for contract in self:
            contract.qty_remaining = sum(line.qty_remaining for line in contract.line_ids)

    @api.depends('line_ids.progress_percentage')
    def _compute_progress(self):
        for contract in self:
            total_qty = sum(line.qty_contract for line in contract.line_ids)
            if total_qty:
                total_sold = sum(line.qty_sold for line in contract.line_ids)
                contract.progress_percentage = (total_sold / total_qty) * 100
            else:
                contract.progress_percentage = 0.0

    def _compute_sale_order_count(self):
        for contract in self:
            contract.sale_order_count = len(contract.sale_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('contract.sale') or _('New')
        return super(ContractSale, self).create(vals_list)

    def action_confirm(self):
        for contract in self:
            if not contract.line_ids:
                raise UserError(_('Không thể xác nhận hợp đồng không có sản phẩm!'))
            if contract.state != 'draft':
                raise UserError(_('Chỉ có thể xác nhận hợp đồng ở trạng thái nháp!'))
            # Check dates
            today = fields.Date.today()
            if contract.date_end < today:
                raise UserError(_('Không thể xác nhận hợp đồng đã hết hạn!'))
        self.write({'state': 'active'})
        return True

    def action_done(self):
        for contract in self:
            if contract.state not in ['active', 'expired']:
                raise UserError(_('Chỉ có thể hoàn thành hợp đồng đang hoạt động hoặc đã hết hạn!'))
        self.write({'state': 'done'})
        return True

    def action_draft(self):
        for contract in self:
            if contract.state != 'active':
                raise UserError(_('Chỉ có thể hoàn về nháp từ trạng thái đang hoạt động!'))
            # Check if there are confirmed SOs
            confirmed_so = contract.sale_order_ids.filtered(
                lambda so: so.state in ['sale', 'done']
            )
            if confirmed_so:
                raise UserError(_('Không thể hoàn về nháp. Đã có đơn bán hàng được xác nhận!'))
        self.write({'state': 'draft'})
        return True

    def action_view_sale_orders(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('sale.action_orders')
        action['domain'] = [('contract_id', '=', self.id)]
        action['context'] = {'default_contract_id': self.id}
        return action

    @api.model
    def _cron_check_expired_contracts(self):
        today = fields.Date.today()
        expired_contracts = self.search([
            ('state', '=', 'active'),
            ('date_end', '<', today)
        ])
        expired_contracts.write({'state': 'expired'})
        return True

    @api.model
    def _cron_send_alerts(self):
        today = fields.Date.today()
        threshold_days = 30  # days before expiry
        qty_threshold = 20.0  # percentage

        # Check for low quantity
        low_qty_contracts = self.search([
            ('state', '=', 'active'),
            ('alert_sent', '=', False),
        ])
        for contract in low_qty_contracts:
            for line in contract.line_ids:
                if line.qty_contract > 0:
                    remaining_pct = (line.qty_remaining / line.qty_contract) * 100
                    if remaining_pct < qty_threshold:
                        contract._send_low_quantity_alert()
                        contract.alert_sent = True
                        break

        # Check for near expiry
        near_expiry_contracts = self.search([
            ('state', '=', 'active'),
            ('expiry_alert_sent', '=', False),
            ('date_end', '<=', today + timedelta(days=threshold_days)),
        ])
        for contract in near_expiry_contracts:
            contract._send_expiry_alert()
            contract.expiry_alert_sent = True

        return True

    def _send_low_quantity_alert(self):
        self.ensure_one()
        template = self.env.ref('contract_sale.email_template_contract_low_qty')
        if template:
            template.send_mail(self.id, force_send=True)
        # Post to chatter
        self.message_post(
            body=_('Cảnh báo: Số lượng hợp đồng đang thấp (còn %.2f%%)!'),
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    def _send_expiry_alert(self):
        self.ensure_one()
        template = self.env.ref('contract_sale.email_template_contract_expiry')
        if template:
            template.send_mail(self.id, force_send=True)
        self.message_post(
            body=_('Cảnh báo: Hợp đồng sắp hết hạn (trong vòng 30 ngày)!'),
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    def write(self, vals):
        # Prevent editing lines when contract is active
        if any(contract.state == 'active' for contract in self):
            restricted_fields = ['partner_id', 'date_start', 'date_end']
            if any(field in vals for field in restricted_fields):
                raise UserError(_('Không thể sửa hợp đồng khi đang hoạt động!'))
        return super(ContractSale, self).write(vals)

    def unlink(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError(_('Chỉ có thể xóa hợp đồng ở trạng thái nháp!'))
        return super(ContractSale, self).unlink()
