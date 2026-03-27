import json

from odoo import http, _
from odoo.http import request, _logger
from odoo.tools import date_utils


class MainApi(http.Controller):

    @http.route(['/download/stream_api'], type='http', cors=False, auth="none", csrf=False,
                methods=['PUT', 'POST', 'GET'])
    def export_excel(self, **kwargs):
        params = json.loads(request.httprequest.data)
        context = json.loads(params.get('context', False))
        user = request.env.user.browse(request.env.context.get('uid'))
        report = request.env['loilv.base.report'].sudo().browse(int(params.get('id')))
        try:
            data = report.with_user(user).with_context(context).get_excel_file(params.get('model', False), params.get('id'))
        except Exception as e:
            return request.make_response(data=json.dumps({'error': str(e)}), status=400)

        # Tạo response HTTP
        response = request.make_response(
            data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=export_excel.xlsx;')
            ])

        return response

    @http.route(['/preview/stream_api'], type='http', cors=False, auth="none", csrf=False,
                methods=['PUT', 'POST', 'GET'])
    def preview_excel(self, **kwargs):
        params = json.loads(request.httprequest.data)
        context = json.loads(params.get('context', False))
        user = request.env.user.browse(request.env.context.get('uid'))
        report = request.env['loilv.base.report'].sudo().browse(int(params.get('id')))
        data = report.with_user(user).with_context(context).preview_excel_to_html(params.get('model', False), params.get('id'))
        return json.dumps(data, default=date_utils.json_default)
