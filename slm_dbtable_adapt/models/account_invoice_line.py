# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    registration_number = fields.Integer(
        string="Reg. Number", required=False, )
