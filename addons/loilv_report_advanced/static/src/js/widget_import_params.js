/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
// import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useState, onWillStart} from "@odoo/owl";
import {loadJS} from "@web/core/assets";
// import {_t} from "@web/core/l10n/translation";
// import { Many2ManyField } from "@web/views/fields/many2many/many2many_field";
import {Many2ManyTagsField} from "@web/views/fields/many2many_tags/many2many_tags_field";

export class ExcelMany2ManyField extends Many2ManyTagsField {
    async setup() {
        super.setup();
        this.state = useState({
            files: [],
            loading: false,
            error: this.props.value.context.field ? null : 'Thiếu field trong context, vui lòng liên hệ quản trị viên!',
            isImport: false,
            countRecord: 0
        });

        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        onWillStart(async () => {
            loadJS("/loilv_report_advanced/static/lib/xlsx.full.min.js")
        });
    }

    // Xử lý import Excel
    async onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;
        if (!this.props.value.context.field) {
            this.state.error = 'Thiếu field trong context, vui lòng liên hệ quản trị viên!';
            return false;
        }

        this.state.loading = true;
        this.state.error = null;

        try {
            const data = await this.readFileAsArrayBuffer(file);
            const workbook = XLSX.read(data, {type: 'array'});
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const listData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 }).slice(1).map(row => row[0]).filter(value => value !== undefined && value !== null);
            if (listData.length > 0) {
                await this.processExcelData(listData);
                if (!this.state.error) {
                this.notification.add('Nhập dữ liệu từ file thành công.', {
                    type: "success",
                });
                }
            } else {
                this.state.error = 'File import dữ liệu trống, vui lòng kiểm tra lại';
            }
        } catch (error) {
            this.state.error = error.message;
            this.notification.add("Có lỗi xảy ra trong quá trình nhập dữ liệu từ file.", {
                type: "danger",
            });
        } finally {
            this.state.loading = false;
            ev.target.value = null;
        }
    }

    readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsArrayBuffer(file);
        });
    }

    async processExcelData(listData) {
        try {
            const {error_message, ids, counts} = await this.orm.call(
                'ir.model',
                "search_create_excel_records",
                [this.props.relation, listData, this.props.value.context.field],
            );
            if (error_message) {
                this.state.error = error_message;
            } else {
                await this.props.value.replaceWith(ids);
                this.state.countRecord = counts;
                this.state.isImport = true;
            }
        } catch (error) {
            throw new Error("Failed to process Excel data");
        }
    }

    // Tải template Excel
    downloadTemplate() {
        const fieldSearch = this.props.value.context.field;
        const ws = XLSX.utils.json_to_sheet([{[fieldSearch]: ""}]);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Template");
        XLSX.writeFile(wb, "import_template.xlsx");
    }

    async btnRemoveValue() {
        await this.props.value.replaceWith([]);
        this.state.isImport = false;
        this.state.countRecord = 0;
        this.state.error = null;
    }
}

ExcelMany2ManyField.template = "loilv_report_advanced.ExcelMany2Many";
ExcelMany2ManyField.components = {
    ...Many2ManyTagsField.components,
};
ExcelMany2ManyField.props = {
    ...Many2ManyTagsField.props,
};
ExcelMany2ManyField.defaultProps = {
    ...Many2ManyTagsField.defaultProps,
};

export const excelMany2ManyField = {
    component: ExcelMany2ManyField,
    supportedTypes: Many2ManyTagsField.supportedTypes,
    extractProps: Many2ManyTagsField.extractProps,
};

registry.category("fields").add("excel_many2many", excelMany2ManyField);