/** @odoo-module **/
import {FormRenderer} from "@web/views/form/form_renderer";
import {loadJS} from "@web/core/assets";

import {formView} from '@web/views/form/form_view';
import {registry} from "@web/core/registry"

const {useRef, onPatched, onMounted, useState, onWillStart, onRendered} = owl;

export class LoilvReportAdvancedRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.headers = useState({
            data: []
        })
        this.dataTable = null
        onWillStart(() =>
            loadJS("/loilv_report_advanced/static/src/libs/datatables.min.js")
        );

        onRendered(() => {
            const table = this.dataTable;
            if (table) {
                table.on('click', 'tbody tr', (e) => {
                    let classList = e.currentTarget.classList;

                    if (classList.contains('active')) {
                        classList.remove('active');
                    } else {
                        table.rows('.active').nodes().each((row) => row.classList.remove('active'));
                        classList.add('active');
                    }
                });
            }
        })
    }

    async previewData() {
        const self = this
        const root = this.env.model.root
        await root.save()
        const model = root.resModel
        const id = root.data.id
        self.env.services.ui.block();

        try {
            const response = await fetch('/preview/stream_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    'model': model,
                    'id': id,
                    'company_id': this.env.model.root.context.allowed_company_ids,
                    'context': JSON.stringify(root.context)
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                const error = JSON.parse(errorText)
                console.log(error, 'error')
                this.env.services.notification.add(error['error'], {type: 'danger'});
                return false;
            }

            const reader = response.body.getReader();
            let result = '';

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                result += new TextDecoder().decode(value);
            }

            const data = JSON.parse(result);

            if (data.length && !data[0]) {
                this.env.services.notification.add(data[1][0]);
                return;
            }

            // ... rest of the function remains the same
            self.headers.data = data.length === 0 ? [] : data[0].map(t => ({'title': t}));
            if (self.headers.data.length === 0 || (Array.isArray(data) && data.length === 0)) {
                if (self.dataTable) {
                    self.dataTable.clear().draw();
                }
                this.env.services.notification.add('Không có dữ liệu!');
                return;
            }

            if (self.dataTable) {
                self.dataTable.clear().destroy();
                $('#table-preview').html()
            }

            self.dataTable = $('#table-preview').DataTable({
                columns: self.headers.data,
                data: data[1],
                pageLength: 50,
                order: [],
            });
        } catch
            (error) {
            console.log('Download failed:', error);
            // Hiển thị thông báo lỗi cho người dùng
            this.env.services.notification.add('Có lỗi xảy ra. Vui lòng thử lại sau.');
        } finally {
            self.env.services.ui.unblock();
        }
    }

    async downloadData() {
        const self = this;
        const root = this.env.model.root;
        await root.save();
        const model = root.resModel;
        const id = root.data.id;

        self.env.services.ui.block();

        try {
            const response = await fetch('/download/stream_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: model,
                    id: id,
                    company_id: this.env.model.root.context.allowed_company_ids,
                    context: JSON.stringify(root.context),
                }),
            });

            if (!response.ok) {
                const errorText = await response.text();
                const error = JSON.parse(errorText)
                console.log(error, 'error')
                this.env.services.notification.add(error['error'], {type: 'danger'});
                return false;
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${root.data.display_name}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (error) {
            console.error('Download failed:', error);
            // Hiển thị thông báo lỗi chi tiết từ server nếu có
            const errorMessage = error.message || 'Không thể tải xuống tệp. Vui lòng thử lại sau.';
            this.env.services.notification.add(errorMessage, {type: 'danger'});
        } finally {
            self.env.services.ui.unblock();
        }
    }

}

export const
    JsClassExportExcel = {
        ...formView,
        Renderer: LoilvReportAdvancedRenderer
    };
registry
    .category(
        "views"
    ).add(
    "loilv_report_advanced_form"
    ,
    JsClassExportExcel
)
;
