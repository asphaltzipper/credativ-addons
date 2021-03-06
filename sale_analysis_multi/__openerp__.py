# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution   
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sales Analyis User Currency',
    'version': '0.1',
    'category': 'Sales & Purchases',
    'description':
        """
        Sale Order Analysis view in User currency. This module calculates all sales total into exisiting user's' currency
        """,
    'author': 'Credativ Ltd',
    'website' : 'http://credativ.co.uk',
    'depends': [
        'sale',
        'sale_stock',
        ],
    'init_xml': [
        ],
    'data': [
        'security/ir.model.access.csv',
        'sale_report_view.xml',
    ],
    'demo_xml': [
    ],
    'installable': True,
    'active': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
