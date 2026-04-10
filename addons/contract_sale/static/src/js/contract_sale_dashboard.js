/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";

export const contractSaleDashboardKanbanView = {
    ...kanbanView,
    buttonTemplate: "contract_sale.DashboardKanbanView.Buttons",
};

registry.category("views").add("contract_sale_dashboard_kanban", contractSaleDashboardKanbanView);
