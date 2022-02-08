# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'General Ledger Updation',
    'version': '12.0.1',
    'author': 'xetechs',
    'website': 'https://xetechs.com',
    'category': 'Account',
    'summary': 'General Ledger Updation',
    'description': '''
''',
    'depends': ['account', 'account_reports'],
    'data': [
        'wizard/payment_register_wiz.xml',
        'views/account_payment_view.xml',
        'views/account_invoice_view.xml',
        'views/account_reports.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
