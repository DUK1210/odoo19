from odoo import fields, api, models, SUPERUSER_ID
import os
import xml.etree.ElementTree as ET

from odoo.modules import get_module_path

FIELD_TYPES = [
    ('char', 'char'),
    ('integer', 'integer'),
    ('float', 'float'),
    ('boolean', 'boolean'),
    ('text', 'text'),
    ('date', 'date'),
    ('datetime', 'datetime'),
    ('selection', 'selection'),
    ('many2one', 'many2one'),
    ('many2many', 'many2many')
]


class LoiLVReportSetup(models.Model):
    _name = 'loilv.report.list'
    _description = 'Cấu hình báo cáo'

    name = fields.Char(string='Tên báo cáo')
    report_type = fields.Selection([
        ('stock', 'Báo cáo kho'),
        ('sale', 'Báo cáo bán hàng'),
        ('purchase', 'Báo cáo mua hàng'),
        ('accounting', 'Báo cáo kế toán'),
        ('other', 'Báo cáo khác'),
    ], string='Loại báo cáo')
    model_name = fields.Char(string='Tên model')
    query_string = fields.Text(string='Câu truy vấn')
    title_json = fields.Text('Json title', default={})
    setup_params = fields.One2many('loilv.report.setup.parameter', 'report_id', string='Cấu hình đầu vào')
    access_ids = fields.One2many('loilv.report.access', 'report_id', string='Cấu hình quyền')
    model_id = fields.Many2one('ir.model', copy=False)
    view_id = fields.Many2one('ir.ui.view', copy=False)
    action_id = fields.Many2one('ir.actions.act_window', copy=False)
    menu_id = fields.Many2one('ir.ui.menu', copy=False)
    limit = fields.Integer(string='Số ngày giới hạn')
    version2 = fields.Boolean(string='Version 2', default=False)

    def create_view_from_xml(self):
        ir_view = self.env['ir.ui.view']
        path = os.path.join(get_module_path('loilv_report_advanced'), 'data', 'xml_default.txt')
        with open(path, 'r', encoding='utf-8') as file:
            xml_string = file.read()
        xml_string_from_tree = xml_string
        string_left = ''
        string_right = ''
        for param in self.setup_params:
            if param.ttype == 'many2many':
                field_str = """
                <field name="x_%s" widget='many2many_tags' options=\"{'no_create': True}\"/>
                """ % (param.name)
            elif param.ttype == 'many2one':
                field_str = """
                <field name="x_%s" options=\"{'no_create': True}\"/>
                """ % (param.name)
            else:
                field_str = """
                <field name="x_%s"/>
                """ % (param.name)

            if param.group == '1':
                string_left += field_str
            else:
                string_right += field_str
        xml_string = xml_string_from_tree % (
            string_left,
            string_right
        )
        return ir_view.create({
            "name": self.name,
            "model": f"x_{self.model_name}",
            "type": "form",
            "mode": "primary",
            "active": True,
            "arch_prev": xml_string,
            "arch_db": xml_string

        })

    def create_action_menu(self):
        ir_action = self.env['ir.actions.act_window']
        ir_action = ir_action.create({
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': f"x_{self.model_name}",
            'view_mode': "form",
            'context': {
                'default_x_res_id': self.id,
                'default_x_res_model': self._name,
                'default_x_name': self.name
            }
        })

        menu = self.env['ir.ui.menu'].create({
            'name': self.name,
            'parent_id': self.env.ref('loilv_report_advanced.loilv_setup_report_public_root').id,
            'action': 'ir.actions.act_window,{}'.format(ir_action.id),
        })
        self.menu_id = menu.id
        self.action_id = ir_action.id
        return ir_action

    def prepare_data_model(self):
        params = []
        for param in self.setup_params:
            if f"x_{param.name}" in self.model_id.field_id.mapped('name'):
                continue
            params.append((0, 0, {
                'name': f"x_{param.name}",
                'field_description': param.description,
                'ttype': param.ttype,
                'required': param.required,
                'relation': param.relation,
                'domain': param.domain,
                'relation_table': param.many2many_model,
                'column1': param.column_1,
                'column2': param.column_2,
                'selection_ids': [(0, 0, {'value': s.name, 'name': s.display}) for s in param.selection_ids]
            }))
        if not self.model_id:
            params += [
                (0, 0, {
                    'name': f"x_res_id",
                    'field_description': 'Report',
                    'ttype': 'integer',
                }),
                (0, 0, {
                    'name': f"x_res_model",
                    'field_description': 'Report',
                    'ttype': 'char',
                }),
                (0, 0, {
                    'name': f"x_name",
                    'field_description': 'Name',
                    'ttype': 'char',
                })
            ]

        access = []
        if not self.model_id.access_ids:
            for _ac in self.access_ids:
                access.append((0, 0, {
                    'name': _ac.name,
                    'group_id': _ac.group_id.id,
                    'perm_read': _ac.perm_read,
                    'perm_write': _ac.perm_write,
                    'perm_create': _ac.perm_create

                }))
        return params, access

    def prepare_value_create_model_report(self):

        return {
            'name': self.name,
            'model': f"x_{self.model_name}",
            'transient': True,
            'state': 'manual',
            'field_id': self.prepare_data_model()[0],
            'access_ids': self.prepare_data_model()[1]
        }

    def confirm(self):
        self.update_model()
        if not self.model_id:
            report_model = self.env['ir.model'].create(self.prepare_value_create_model_report())
            self.model_id = report_model.id
        report_view = self.create_view_from_xml()
        self.view_id = report_view.id
        if not self.action_id:
            action = self.create_action_menu().read()[0]
        else:
            action = self.action_id.read()[0]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Đã tạo thành công báo cáo %s' % self.name,
                'type': 'success',
                'sticky': False,
                'next': action,
            }
        }

    def update_model(self):
        if self.model_id and self.view_id:
            self.view_id.sudo().unlink()
            self.model_id.sudo().write({
                'field_id': self.prepare_data_model()[0],
                'access_ids': self.prepare_data_model()[1],
            })

    def unlink(self):
        for rec in self:
            if rec.model_id and rec.view_id:
                self.env[self.model_id.model].search([]).sudo().unlink()
                rec.action_id.sudo().unlink()
                rec.menu_id.sudo().unlink()
                rec.view_id.sudo().unlink()
                rec.model_id.sudo().unlink()
        return super().unlink()

    def view_report(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': f"x_{self.model_name}",
            'view_id': False,
            'view_mode': 'form',
            'context': {
                'default_x_res_id': self.id,
                'default_x_res_model': self._name,
                'default_x_name': self.name,
            },
            'target': 'current',
        }

    def write_query_string(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('loilv_report_advanced.loilv_report_list_view_view_form_query').id, 'form')],
            'target': 'current',
        }

    def write_title_excel(self):
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('loilv_report_advanced.loilv_report_list_view_view_form_json').id, 'form')],
            'target': 'current',
        }


class LoiLVReportSetupParameter(models.Model):
    _name = 'loilv.report.setup.parameter'
    _description = 'Cấu hình đầu vào báo cáo'

    report_id = fields.Many2one('loilv.report.list')
    name = fields.Char(string='Tên trường', required=True)
    description = fields.Char(string='Mô tả trường', required=True)
    ttype = fields.Selection(selection=FIELD_TYPES, string='Kiểu dữ liệu', required=True)
    relation = fields.Char(string='Tên model quan hệ')
    domain = fields.Char(string='Tên miền')
    many2many_model = fields.Char(string='Bảng trung gian')
    column_1 = fields.Char(string='Cột 1')
    column_2 = fields.Char(string='Cột 2')
    group = fields.Selection([('1', 'Hiển thị trái'), ('2', 'Hiển thị phải')], string='Cách hiển thị', required=True)
    required = fields.Boolean(string='Bắt buộc', default=False)
    selection_ids = fields.One2many("loilv.report.setup.parameter.selection", "setup_id", string="Danh sách lựa chọn", copy=True)


class SelectionSetup(models.Model):
    _name = 'loilv.report.setup.parameter.selection'
    _description = 'Cấu hình đầu vào báo cáo'

    setup_id = fields.Many2one('loilv.report.setup.parameter')
    name = fields.Char(string='Tên')
    display = fields.Char(string='Tên hiển thị')


class LoiLVReportResponseSetup(models.Model):
    _name = 'loilv.report.setup.response'
    _description = 'Cấu hình đầu ra báo cáo'

    name = fields.Char(string='Tên truờng')
    description = fields.Char(string='Mô tả')


class LoilvReportAccess(models.Model):
    _name = 'loilv.report.access'
    _description = 'Quyền truy cập báo cáo'

    report_id = fields.Many2one('loilv.report.list')
    name = fields.Char(string='Tên quyền')
    group_id = fields.Many2one('res.groups', string='Nhóm quyền')
    perm_read = fields.Boolean(string='Quyền đọc', default=True)
    perm_write = fields.Boolean(string='Quyền ghi', default=True)
    perm_create = fields.Boolean(string='Quyền tạo', default=True)
