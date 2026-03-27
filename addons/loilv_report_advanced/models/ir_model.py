from odoo import fields, api, models
from odoo.exceptions import UserError


class InheritModel(models.Model):
    _inherit = 'ir.model'
    @api.model
    def search_create_excel_records(self, model, list_data, field):
        try:
            self._cr.execute(f"""select json_agg(distinct id) from {model.replace('.', '_')} where {field} = any (array {list_data})""")
            ids = self._cr.fetchone()[0] or []
            if ids:
                self._cr.execute(f"""select count(distinct {field}) from {model.replace('.', '_')} where {field} = any (array {list_data})""")
                error_message, counts = None, self._cr.fetchone()[0] or 0
            else:
                error_message, ids, counts = 'Không có dữ liệu thỏa mãn với dữ liệu trong file excel', None, 0
        except Exception as e:
            error_message, ids, counts = f"Lỗi nhập liệu từ file: {str(e)}", None, 0
        return {"error_message": error_message, "ids": ids, "counts": counts}
