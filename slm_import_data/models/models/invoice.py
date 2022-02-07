# -*- coding: utf-8 -*-

import json
import re
import uuid
from functools import partial
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode
from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, pycompat, date_utils
from odoo.tools.misc import formatLang
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from odoo.addons import decimal_precision as dp

class AccountInvoice(models.Model):
	_inherit = "account.invoice"
	
	
	@api.model
	def _run_create_invoice_edgar(self):
		self.create_invoice_edgar()
		
	@api.multi
	def create_invoice_edgar(self):
		cr = self.env.cr
		#invoice_line_obj = self.env['account.invoice.line']
		invoice_obj = self.env['account.invoice']
		inv = {}
		inv_line = []
		item = 0
		try:
			query = ('''select se.pnrr as pnr from slm_edgard se where se.sheet_name = 'SALES JOURN' group by pnr;''')
			cr.execute(query,[])
			for pnr in cr.dictfetchall():
				inv_line = []
				#raise UserError(_('%s')%(pnr))
				sql = ('''select se.id as id, se.company_id as company_id, se.branch_code as branch_code, se.day_book as day_book, se.piece_number as piece_number,\
							se.registration_number as registration_number, se.book_year as book_year, se.period as period, se.account_number as account_number,\
							se.cost_center as cost_center, se.invoice_number as invoice_number, se.description as description, se.currency_code as currency_code,\
							se.amount as amount, se.amount_srd as amount_srd, se.amount_usd as amount_usd, se.operation_code, se.date as date, se.date_read as date_read,\
							se.ticketnumber as ticketnumber, se.row_count as row_count, se.pnrr as pnr\
							from slm_edgard se\
							where se.sheet_name = 'SALES JOURN' and se.pnrr = %s;''')
				cr.execute(sql,[pnr['pnr']])
				for row in cr.dictfetchall():
					item += 1
					line = self.create_invoice_line_edgar(row)
					inv_line.append((0,0, line))
					inv = {
						'partner_id': 2682,
						'number': row.get('pnr', ""),
						'move_name': row.get('pnr', ""),
						'date_invoice': datetime.strptime(str(row['date']),'%Y-%m-%d %H:%M:%S').date(),
						'journal_id': 20,
						#'branch_id': self.get_branch(row['branch_code']) or False,
						'company_id': 2,
						'account_id': 744,
						'piece_number': row.get('piece_number', ""),
						'reference': row.get('ticketnumber', ""),
						'book_year': row.get('book_year', ""),
						'period': row.get('period',""),
						'type': 'out_invoice',
						'state': 'draft',
						'invoice_line_ids': inv_line,
					}
				invoice_obj.create(inv)
				#if item == 1:
				cr.commit()
				#item = 0
		except Exception as e:
			#raise UserError(_('%s')%(e))
			print(e)
			cr.rollback()
			pass
		
	@api.multi
	def create_move_margo(self):
		cr = self.env.cr
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		move = {}
		move_lines = []
		num_line = 0
		log_file = "Journal Entries Log"
		#try:
		sql = ('''select sm.sheet_name as sheet_name \
					from slm_edgard sm \
					where sm.sheet_name != 'SALES JOURN' \
					group by sm.sheet_name;''')
		cr.execute(sql,[])
		for row in cr.dictfetchall():
			move_lines = self.get_move_lines(row)
			if move_lines:
				num_line += 1
				debit = move_lines[3]
				credit = move_lines[4]
				move = {
					#'journal_id': self.get_journal(move_lines[1]),
					'journal_id': 20,
					'date': datetime.strptime(str(move_lines[2]),'%Y-%m-%d %H:%M:%S').date(),
					'company_id': 2,
					'ref': "%s %s" %(row['sheet_name'], datetime.strptime(str(move_lines[2]),'%Y-%m-%d %H:%M:%S').date()),
					'line_ids': move_lines[0],
				}
				try:
					move_obj.create(move)
					cr.commit()
					log_file += "Line : %s Sheet name: %s -> Successful" %(num_line, row['sheet_name'])
					return log_file
				except exceptions as ex:
					print(ex)
					log_file += "Line : %s Sheet name: %s Error: %s " %(num_line, row['sheet_name'], ex)
					log_gile += "\n"
					cr.rollback()
					pass
					return log_file
		#except Exception as e:
		#print(e)
		#pass
		#return log_file

	@api.multi
	def get_move_lines(self, row):
		cr = self.env.cr
		lines = []
		line = {}
		date = False
		day_book = False
		debit = 0.00
		credit = 0.00
		if row:
			sql = ('''select se.id as id , se.company_id as company_id, se.branch_code as branch_code, se.day_book as day_book, se.piece_number as piece_number,\
						se.registration_number as registration_number, se.book_year as book_year, se.period as period, se.account_number as account_number,\
						se.cost_center as cost_center, se.invoice_number as invoice_number, se.description as description, se.currency_code as currency_code,\
						COALESCE(round(se.amount::numeric,2),0.00) as amount, COALESCE(round(se.amount_srd::numeric,2),0.00) as amount_srd, COALESCE(round(se.amount_usd::numeric,2), 0.00) as amount_usd, se.operation_code, se.date as date,\
						se.date_read as date_read, se.row_count as row_count\
						from slm_edgard se\
						where se.sheet_name = %s;''')
			cr.execute(sql,[row['sheet_name']])
			for l in cr.dictfetchall():
				day_book = l['day_book']
				date = l['date']
				if l['amount'] > 0.00:
					debit += l['amount']
					line = {
						'account_id': self.get_account(l['account_number'], l['branch_code']),
						'name': l['description'] or "",
						#'branch_id': self.get_branch(l['branch_code']) or False,
						'analytic_account_id': self.get_analytic_account(l['cost_center']),
						'debit': abs(l['amount']) or 0.00,
						'credit': 0.00,
						'bedrsrd': float(l['amount_srd']) or 0.00,
						'bedrusd': float(l['amount_usd']) or 0.00,
						'faktnr': str(l['invoice_number']),
						'omschr': str(l['description']),
						}
				elif l['amount'] < 0.00:
					credit += l['amount']
					line = {
						'account_id': self.get_account(l['account_number'], l['branch_code']),
						'name': l['description'] or "",
						#'branch_id': self.get_branch(l['branch_code']) or False,
						'analytic_account_id': self.get_analytic_account(l['cost_center']),
						'debit': 0.00,
						'credit': abs(l['amount']) or 0.00,
						'bedrsrd': float(l['amount_srd']) or 0.00,
						'bedrusd': float(l['amount_usd']) or 0.00,
						'faktnr': str(l['invoice_number']),
						'omschr': str(l['description']),
					}
				lines.append((0,0,line))
		return lines, day_book, date, debit, credit
			
	@api.multi
	def create_invoice_line_edgar(self, row):
		line = {}
		if row:
			line = {
				'name': row['description'] or "",
				'account_id': self.get_account(row['account_number'], row['branch_code']) or False,
				'quantity': 1.00,
				'price_unit': row['amount'],
				'registration_number': row['registration_number'],
				'analytic_account_ids': False,
			}
		return line
	
	@api.multi
	def get_analytic_account(self, analytic_account):
		#account_obj = self.env['account.account']
		analytic_obj = self.env['account.analytic.account']
		#analytic_account_obj = self.env['account.analytic.tag']
		account_id = False
		#company_id = False
		if analytic_account:
			#if branch_code:
			#company_id = self.get_company(branch_code)
			account_id = analytic_obj.search([('code', '=', analytic_account)], limit=1)
		return account_id and account_id.id or False
	
	@api.multi
	def get_branch(self, branch_code):
		branch_obj = self.env['res.branch']
		#res = False
		branch_id = False
		if branch_code:
			branch_id = branch_obj.search([('branch_code', '=', branch_code)], limit=1)
		return branch_id.id
	
	@api.multi
	def get_account(self, account_number, branch_code):
		account_obj = self.env['account.account']
		account_id = False
		company_id = False
		if account_number:
			if branch_code:
				company_id = self.get_company(branch_code)
			account_id = account_obj.search([('code', '=', account_number)], limit=1)
		return account_id and account_id.id

	@api.multi
	def get_company(self, branch_code):
		branch_obj = self.env['res.branch']
		#res = False
		branch_id = False
		if branch_code:
			branch_id = branch_obj.search([('branch_code', '=', branch_code)], limit=1)
		return branch_id.company_id.id
	
	@api.multi
	def get_journal(self, day_book):
		journal_obj = self.env['account.journal']
		journal_id = False
		if day_book:
			journal_id = journal_obj.search([('day_book', '=', day_book)], limit=1)
		return journal_id.id
AccountInvoice()