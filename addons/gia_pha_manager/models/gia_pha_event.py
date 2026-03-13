from odoo import fields, models


class GiaPhaEvent(models.Model):
    _name = 'gia.pha.event'
    _description = 'Su kien gia pha'
    _order = 'event_date desc, id desc'

    name = fields.Char(string='Ten su kien', required=True)
    member_id = fields.Many2one('gia.pha.member', string='Thanh vien', required=True, ondelete='cascade')
    event_type = fields.Selection([
        ('birth', 'Sinh nhat'),
        ('marriage', 'Ket hon'),
        ('death_anniversary', 'Gio / Ky gio'),
        ('achievement', 'Thanh tuu'),
        ('other', 'Khac'),
    ], string='Loai su kien', default='other', required=True)
    event_date = fields.Date(string='Ngay su kien', required=True)
    description = fields.Text(string='Mo ta')
    location = fields.Char(string='Dia diem')
