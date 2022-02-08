# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class CashboxLine(models.Model):
	_inherit = 'account.cashbox.line'
	
	currency_id = fields.Many2one('res.currency', string="Currency", required=True, readonly=False)
	journal_id = fields.Many2one('account.journal', 'Journal', required=True, readonly=False)
	cash_session_id = fields.Many2one('cash.session', related="cashbox_id.cash_session_id", string="Session", copy=False)

	@api.onchange('journal_id', 'currency_id')
	def onchange_journal(self):
		if self.journal_id:
			self.currency_id = self.journal_id.currency_id

CashboxLine()

class AccountBankStmtCashWizard(models.Model):
	_inherit = 'account.bank.statement.cashbox'

	cash_session_id = fields.Many2one('cash.session', string="Session", copy=False)

	@api.multi
	def validate(self):
		#get cash session
		session_id = self.env.context.get('active_id', False)
		session_obj = self.env['cash.session']
		bnk_stmt_obj = self.env['account.bank.statement']
		#bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
		total = 0.0
		#balance_start = 0.00
		#raise UserError(_("%s") %(bnk_stmt_id))
		for session in session_obj.browse(session_id):
			#balance_start = session.cash_register_balance_start
			for l in session.statement_ids:
				total = 0.00
				if l.journal_id.type == 'cash':
					for lines in self.cashbox_lines_ids:
						if (l.journal_id.currency_id.id == lines.currency_id.id) and (l.journal_id.id == lines.journal_id.id):
							total += lines.subtotal
				if self.env.context.get('balance', False) == 'start':
					#starting balance
					#balance_start = session.cash_register_balance_start
					l.write({'balance_start': (l.balance_start + total), 'cashbox_start_id': self.id})
				else:
					#closing balance
					l.write({'balance_end_real': total, 'cashbox_end_id': self.id})
		return {'type': 'ir.actions.act_window_close'}

AccountBankStmtCashWizard()