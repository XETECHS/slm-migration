# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import re


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _default_session(self):
        return self.env['cash.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

    session_id = fields.Many2one(
        'cash.session', string='Session', required=False, index=True,
        domain="[('state', '=', 'opened')]", states={'draft': [('readonly', False)]},
        readonly=True, default=_default_session)
    picking_id = fields.Many2one(
        'stock.picking', string='Picking', readonly=True, copy=False)
    statement_ids = fields.One2many('account.bank.statement.line', 'cash_statement_id', string='Payments', states={
                                    'draft': [('readonly', False)]}, readonly=True)
    invoice_number = fields.Char(string='Invoice Number', readonly=True,
                                 states={'draft': [('readonly', False)]})
    journal_ids = fields.Many2many(
        'account.journal',
        related='session_id.journal_ids',
        readonly=True,
        string='Available Payment Methods')

    def _write(self, values):
        if 'invoice_number' in values:
            inv = values["invoice_number"]
            if inv:
                inv = re.sub('\ |\?|\.|\!|\/|\;|\:|\-|\,', '', inv)
                inv = inv.upper()
                values["invoice_number"] = inv
        res = super(AccountPayment, self)._write(values)
        return res

    @api.model
    def create(self, values):
        if 'invoice_number' in values:
            inv = values["invoice_number"]
            if inv:
                inv = re.sub('\ |\?|\.|\!|\/|\;|\:|\-|\,', '', inv)
                inv = inv.upper()
                values["invoice_number"] = inv
        res = super(AccountPayment, self).create(values)
        return res

    def _prepare_bank_statement_line_payment_values(self, data):
        """Create a new payment for the order"""
        args = {
            'amount': data['amount'],
            'date': data.get('payment_date', fields.Date.context_today(self)),
            'name': self.name,
            'is_internal': data.get('is_internal', False),
            'partner_id': self.env["res.partner"]._find_accounting_partner(self.partner_id).id or False,
        }

        journal_id = data.get('journal', False)
        statement_id = data.get('statement_id', False)
        assert journal_id or statement_id, "No statement_id or journal_id passed to the method!"

        journal = self.env['account.journal'].browse(journal_id)
        # use the company of the journal and not of the current user
        if data['amount'] < 0.00:
            company_cxt = dict(
                self.env.context, force_company=journal.company_id.id)
            account_def = self.env['ir.property'].with_context(
                company_cxt).get('property_account_payable_id', 'res.partner')
            args['account_id'] = (self.partner_id.property_account_payable_id.id) or (
                account_def and account_def.id) or False
        else:
            company_cxt = dict(
                self.env.context, force_company=journal.company_id.id)
            account_def = self.env['ir.property'].with_context(company_cxt).get(
                'property_account_receivable_id', 'res.partner')
            args['account_id'] = (self.partner_id.property_account_receivable_id.id) or (
                account_def and account_def.id) or False

        if not args['account_id']:
            if not args['partner_id']:
                msg = _('There is no receivable account defined to make payment.')
            else:
                msg = _('There is no receivable account defined to make payment for the partner: "%s" (id:%d).') % (
                    self.partner_id.name, self.partner_id.id,)
            raise UserError(msg)

        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        for statement in self.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == journal_id:
                statement_id = statement.id
                break
        if not statement_id:
            raise UserError(_('You have to open at least one cashbox.'))

        args.update({
            'statement_id': statement_id,
            'cash_statement_id': self.id,
            'journal_id': journal_id,
            'ref': self.session_id.name,
        })

        return args

    def add_payment(self, data):
        """Create a new payment"""
        self.ensure_one()
        args = self._prepare_bank_statement_line_payment_values(data)
        context = dict(self.env.context)
        context.pop('pos_session_id', False)
        self.env['account.bank.statement.line'].with_context(
            context).create(args)
        self.amount_paid = sum(
            payment.amount for payment in self.statement_ids)
        return args.get('statement_id', False)

    def post(self):
        config = self.env['cash.config'].search(
            [('user_id', '=', self.env.uid)], limit=1).id
        for rec in self:

            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(
                    _("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(
                    ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(
                        _("You have to define a sequence for %s in your company.") % (sequence_code,))

            if not config:
                # Create the journal entry
                amount = rec.amount * \
                    (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                move = rec._create_payment_entry(amount)

                # In case of a transfer, the first journal entry created debited the source liquidity account and credited
                # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
                if rec.payment_type == 'transfer':
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(amount)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()

                rec.write({'state': 'posted', 'move_name': move.name})

            if config:
                move = False
                # Create the journal entry with session
                #rec.write({'state': 'posted'})
                # if config:
                monto = self.amount or 0.0
                if self.payment_type == 'outbound':
                    monto = monto * -1
                    #move = rec._create_payment_entry(monto)
                    data = {
                        'amount':       monto,
                        'payment_date': self.payment_date,
                        'statement_id': False,
                        'payment_name': self.payment_reference,
                        'journal':      self.journal_id.id,
                        'is_internal': True,
                        # 'amount_currency': monto,
                        # 'currency_id': self.currency_id.id,
                    }
                    self.add_payment(data)
                    amount = rec.amount * \
                        (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                    move = rec._create_payment_entry(amount)
                    rec.write({'state': 'posted'})
                elif self.payment_type == 'inbound':
                    monto = monto * 1
                    data = {
                        'amount':       monto,
                        'payment_date': self.payment_date,
                        'statement_id': False,
                        'payment_name': self.payment_reference,
                        'journal':      self.journal_id.id,
                        'is_internal': True,
                        # 'amount_currency': monto,
                        # 'currency_id': self.currency_id.id,
                    }
                    self.add_payment(data)
                    #rec.write({'state': 'posted'})
                    amount = rec.amount * \
                        (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
                    move = rec._create_payment_entry(amount)
                    rec.write({'state': 'posted'})
                elif self.payment_type == 'transfer':
                    monto = monto * 1
                    move = rec._create_payment_entry(monto)
                    transfer_credit_aml = move.line_ids.filtered(
                        lambda r: r.account_id == rec.company_id.transfer_account_id)
                    transfer_debit_aml = rec._create_transfer_entry(monto)
                    (transfer_credit_aml + transfer_debit_aml).reconcile()
                    data = {
                        'amount':       monto * -1,
                        'payment_date': self.payment_date,
                        'statement_id': False,
                        'payment_name': self.payment_reference,
                        'journal':      self.journal_id.id,
                        'is_internal': True,
                        # 'amount_currency': monto * -1,
                        # 'currency_id': self.currency_id.id,
                    }
                    self.add_payment(data)
                    data = {
                        'amount':       monto,
                        'payment_date': self.payment_date,
                        'statement_id': False,
                        'payment_name': self.payment_reference,
                        'journal':      self.destination_journal_id.id,
                        'is_internal': True,
                        # 'amount_currency':  monto,
                        # 'currency_id': self.currency_id.id,
                    }
                    self.add_payment(data)
                    rec.write({'state': 'posted'})
        return True
