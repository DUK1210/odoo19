from odoo import api, fields, models


class GiaPhaMember(models.Model):
    _name = 'gia.pha.member'
    _description = 'Thanh vien gia pha'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    name = fields.Char(string='Ho va ten', required=True, tracking=True)
    code = fields.Char(string='Ma thanh vien', copy=False)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nu'),
        ('other', 'Khac')
    ], string='Gioi tinh', default='male')
    birth_date = fields.Date(string='Ngay sinh')
    death_date = fields.Date(string='Ngay mat')
    generation = fields.Integer(string='Doi thu', default=1)
    hometown = fields.Char(string='Que quan')
    biography = fields.Text(string='Tieu su')
    active = fields.Boolean(default=True)

    parent_father_id = fields.Many2one('gia.pha.member', string='Cha')
    parent_mother_id = fields.Many2one('gia.pha.member', string='Me')
    spouse_id = fields.Many2one('gia.pha.member', string='Vo/Chong')
    child_ids = fields.One2many('gia.pha.member', 'parent_father_id', string='Con (theo cha)')

    event_ids = fields.One2many('gia.pha.event', 'member_id', string='Su kien')
    image_1920 = fields.Image(string='Anh chan dung')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Ma thanh vien phai la duy nhat!')
    ]

    @api.depends('name', 'generation', 'code')
    def _compute_display_name(self):
        for rec in self:
            parts = [rec.name or '']
            if rec.generation:
                parts.append(f'Doi {rec.generation}')
            if rec.code:
                parts.append(f'[{rec.code}]')
            rec.display_name = ' - '.join([p for p in parts if p])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('gia.pha.member') or 'TVMOI'
        return super().create(vals_list)
