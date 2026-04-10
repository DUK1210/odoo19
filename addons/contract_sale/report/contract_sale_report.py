from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ContractSaleReport(models.AbstractModel):
    _name = 'report.contract_sale.report_contract_sale'
    _description = 'Báo cáo hợp đồng bán'

    def _get_report_values(self, docids, data=None):
        docs = self.env['contract.sale'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'contract.sale',
            'docs': docs,
            'data': data,
        }


class ContractSaleDetailReport(models.TransientModel):
    _name = 'contract.sale.detail.report.wizard'
    _description = 'Wizard báo cáo chi tiết hợp đồng'

    date_from = fields.Date(string='Từ ngày', required=True)
    date_to = fields.Date(string='Đến ngày', required=True)
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    state = fields.Selection([
        ('all', 'Tất cả'),
        ('draft', 'Nháp'),
        ('active', 'Đang hoạt động'),
        ('expired', 'Hết hạn'),
        ('done', 'Hoàn thành'),
    ], string='Trạng thái', default='all')

    def action_print_report(self):
        self.ensure_one()
        domain = [
            ('date_start', '>=', self.date_from),
            ('date_start', '<=', self.date_to),
        ]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state != 'all':
            domain.append(('state', '=', self.state))

        contracts = self.env['contract.sale'].search(domain)
        if not contracts:
            raise UserError(_('Không tìm thấy hợp đồng nào với tiêu chí đã chọn!'))

        return self.env.ref('contract_sale.action_report_contract_sale').report_action(contracts)
