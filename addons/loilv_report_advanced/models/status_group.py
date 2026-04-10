from odoo import fields, models, api


class StatusGroup(models.Model):
    _name = 'status.group'
    _description = 'Nhóm trạng thái'
    _rec_name = 'value'

    model = fields.Char(string='Model')
    key = fields.Char(string='Key')
    value = fields.Char(string='Value')
