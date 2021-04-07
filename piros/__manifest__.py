# -*- coding: utf-8 -*-
{
    'name': "piros",

    'summary': "Piros Sales & Purchase extensions",

    'description': "Piros Sales & Purchase extensions",

    'author': "Piros",
    'website': "https://www.piros.be",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.7',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'sale_margin'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/sale_order_report.xml',
        'views/purchase_quotation_report.xml',
        'views/purchase_order_report.xml',
        'views/resources.xml',
        'views/templates.xml',
        'views/mail_send_to_billing.xml',
        'views/sale_report.xml',
        'views/sale_report_templates.xml',
        'data/categories.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
