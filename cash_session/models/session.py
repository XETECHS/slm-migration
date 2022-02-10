# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class Session(models.Model):
    _inherit = 'cash.session'

    def _reconcile_payments_invoices(self, payments):
        invoice_obj = self.env['account.move']
        invoice_number = False
        invoice_ids = []
        if payments:
            for pay in payments:
                if not pay.invoice_ids:
                    if pay.invoice_number:
                        invoice_number = pay.invoice_number
                        invoice_ids = invoice_obj.search(
                            [('move_name', '=ilike', invoice_number)], limit=1)
                    if invoice_ids:
                        for inv in invoice_ids:
                            pay.write({
                                'invoice_ids': [(4, inv.id, None)]
                            })
                            pay.invoice_ids.register_payment(
                                self._get_move_line(pay))
                            inv.write({'state': 'paid'})
                elif pay.invoice_ids:
                    move_line = self._get_move_line(pay)
                    pay.invoice_ids.register_payment(move_line)
                    pay.invoice_ids.write({'state': 'paid'})
        return True

    def _get_move_line(self, payment):
        move_line_obj = self.env['account.move.line']
        move_lines = False
        move_lines = move_line_obj.search(
            [('name', '=', payment.name), ('credit', '!=', 0.00)])
        return move_lines


Session()
