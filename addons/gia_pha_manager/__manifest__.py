{
    'name': 'Gia Pha Manager',
    'summary': 'Quan ly gia pha dong toc',
    'version': '1.0.0',
    'category': 'Tools',
    'author': 'Family Tree Team',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/gia_pha_member_views.xml',
        'views/gia_pha_event_views.xml',
        'views/gia_pha_menu.xml'
    ],
    'application': True,
    'installable': True
}
