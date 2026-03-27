from pathlib import Path

base = Path(__file__).resolve().parent
pot = base / 'dynamic_approval_workflow.pot'
po = base / 'vi.po'
text = pot.read_text(encoding='utf-8')
text = text.replace('"Language-Team: \\n"', '"Language-Team: Vietnamese\\n"\n"Language: vi_VN\\n"')
text = text.replace('"Content-Transfer-Encoding: \\n"', '"Content-Transfer-Encoding: 8bit\\n"')
text = text.replace('"Plural-Forms: \\n"', '"Plural-Forms: nplurals=1; plural=0;\\n"')

translations = {
    'Approvals': 'Phê duyệt',
    'My Approvals': 'Phê duyệt của tôi',
    'Pending My Action': 'Đang chờ tôi xử lý',
    'All Requests': 'Tất cả yêu cầu',
    'Configuration': 'Cấu hình',
    'Approval Workflows': 'Quy trình phê duyệt',
    'Approval User': 'Người dùng phê duyệt',
    'Approval Manager': 'Quản lý phê duyệt',
    'Approval Request': 'Yêu cầu phê duyệt',
    'Approval Requests': 'Yêu cầu phê duyệt',
    'Approval Stages': 'Các bước phê duyệt',
    'Approval Status': 'Trạng thái phê duyệt',
    'Draft': 'Nháp',
    'Pending Approval': 'Chờ phê duyệt',
    'Approved': 'Đã phê duyệt',
    'Rejected': 'Đã từ chối',
    'Returned': 'Trả lại',
    'Reference': 'Mã tham chiếu',
    'Workflow': 'Quy trình',
    'Document': 'Chứng từ',
    'Status': 'Trạng thái',
    'Current Stage': 'Bước hiện tại',
    'Current Approvers': 'Người phê duyệt hiện tại',
    'Approval History': 'Lịch sử phê duyệt',
    'Requested By': 'Người yêu cầu',
    'Deadline': 'Hạn xử lý',
    'Company': 'Công ty',
    'Name': 'Tên',
    'Sequence': 'Thứ tự',
    'Model': 'Mô hình',
    'Filter Domain': 'Miền lọc',
    'Stages': 'Các bước',
    'Action': 'Hành động',
    'Date': 'Ngày',
    'Submit for Approval': 'Gửi phê duyệt',
    'View Requests': 'Xem yêu cầu',
    'Target': 'Đối tượng',
    'Settings': 'Thiết lập',
    'Notes': 'Ghi chú',
    'Search': 'Tìm kiếm',
    'Search Approval Requests': 'Tìm kiếm yêu cầu phê duyệt',
    'Search Configurations': 'Tìm kiếm cấu hình',
    'Overdue': 'Quá hạn',
    'Confirm': 'Xác nhận',
    'Cancel': 'Hủy',
    'Open Document': 'Mở chứng từ',
    'Approve': 'Phê duyệt',
    'Reject': 'Từ chối',
    'Return to Requester': 'Trả lại cho người yêu cầu',
    'Provide a Reason': 'Nhập lý do',
    'Reason': 'Lý do',
    'Reason / Comment': 'Lý do / Ghi chú',
    'Request Details': 'Chi tiết yêu cầu',
    'Requester': 'Người yêu cầu',
    'Requests': 'Yêu cầu',
    'Reset': 'Đặt lại',
    'Dashboard': 'Bảng điều khiển',
    'No Deadline': 'Không có hạn',
    'No Group': 'Không có nhóm',
    'No Requester': 'Không có người yêu cầu',
    'No Stage': 'Không có bước',
    'No Workflow': 'Không có quy trình',
    '(no reason provided)': '(không có lý do)',
    '(none)': '(không có)',
    'Unknown action: %s': 'Hành động không hợp lệ: %s',
    'Please provide a reason before confirming.': 'Vui lòng nhập lý do trước khi xác nhận.',
    'No source document linked to this request.': 'Không có chứng từ nguồn liên kết với yêu cầu này.',
    'No records identified in context (active_model / active_ids).': 'Không xác định được bản ghi trong ngữ cảnh (active_model / active_ids).',
    'Action Required: Approval Request {{ object.name }}': 'Yêu cầu xử lý: Yêu cầu phê duyệt {{ object.name }}',
    'Approval Request: Notify Approver': 'Yêu cầu phê duyệt: Thông báo người phê duyệt',
}

lines = text.splitlines()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    out.append(line)
    if line.startswith('msgid "') and line != 'msgid ""':
        msgid = line[len('msgid "'):-1]
        if i + 1 < len(lines) and lines[i + 1].startswith('msgstr ""'):
            tr = translations.get(msgid)
            if tr:
                out.append(f'msgstr "{tr}"')
                i += 2
                continue
    i += 1

po.write_text('\n'.join(out) + '\n', encoding='utf-8')
remaining = sum(1 for line in out if line == 'msgstr ""')
print('written', po)
print('remaining_empty_msgstr', remaining)