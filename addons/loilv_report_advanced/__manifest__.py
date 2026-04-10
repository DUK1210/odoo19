# -*- coding: utf-8 -*-
{
    'name': "Report Advanced",

    'summary': """GiÃºp táº¡o bÃ¡o cÃ¡o thuáº­n tiá»‡n hÆ¡n""",

    'description': """
    Ä‚n quáº£ nhá»› káº» trá»“ng cÃ¢y ^^!
    """,

    'author': "LOILV",
    'website': "",
    "license": "LGPL-3",

    'category': 'Generic Modules',
    'version': '19.0.1.0.0',

    'depends': [
        'base',
        'web',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/report_setup.xml',
        'views/status_group.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'loilv_report_advanced/static/src/css/**/*',
            'loilv_report_advanced/static/src/xml/**/*',
            'loilv_report_advanced/static/src/js/**/*',
            'loilv_report_advanced/static/lib/xlsx.full.min.js'
        ]
    }
}

