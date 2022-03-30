# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'Account Entry Cancel',
    'summary': """Account Entry Cancel""",
    'version': '15.0.1',
    'author': 'Laxicon Solution',
    'price': 69.0,
    'sequence': 1,
    'currency': 'USD',
    'category': 'Account',
    'website': 'https://www.laxicon.in',
    'support': 'info@laxicon.in',
    'description': """ This module manage to access for account entry cancel or not.
    """,
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'views/account_view.xml',
    ],
    'installable': True,
    'application': True,
}
