# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError


class Session(models.Model):
	_inherit = 'cash.session'
	
	@api.multi
	def _reconcile_payments_invoices(self, payments):
		payments_obj = self.env['account.payment']
		invoice_obj = self.env['account.invoice']
		invoice_number = False
		invoice_ids = []
		if payments:
			for pay in payments:
				if not pay.invoice_ids:
					if pay.invoice_number:
						invoice_number = pay.invoice_number
						invoice_ids = invoice_obj.search([('move_name', '=ilike', invoice_number)], limit=1)
					if invoice_ids:
						for inv in invoice_ids:
							pay.write({
								'invoice_ids': [(4, inv.id, None)]
							})
							pay.invoice_ids.register_payment(self._get_move_line(pay))
							inv.write({'state': 'paid'})
				elif pay.invoice_ids:
					move_line = self._get_move_line(pay)
					#raise UserError(('%s') %(move_line))
					pay.invoice_ids.register_payment(move_line)
					pay.invoice_ids.write({'state': 'paid'})
		return True
	
	@api.multi
	def _get_move_line(self, payment):
		move_line_obj = self.env['account.move.line']
		move_lines = False
		move_lines = move_line_obj.search([('name', '=', payment.name), ('credit', '!=', 0.00)])
		return move_lines
Session()