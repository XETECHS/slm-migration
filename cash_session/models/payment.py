# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
from odoo import api, models


class Payment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('journal_ids', 'session_id', 'payment_type', 'currency_id', 'amount')
    def onchange_journals(self):
        res = {}
        journal_ids = []
        if self.session_id:
            for journal in self.journal_ids:
                journal_ids.append(journal.id)
        if journal_ids:
            if self.payment_type == 'transfer':
                res['domain'] = {'journal_id': [('id', 'in', journal_ids)], 'destination_journal_id': [
                    ('id', 'in', journal_ids)]}
            else:
                res['domain'] = {'journal_id': [('id', 'in', journal_ids)]}
        return res

    @api.onchange('amount', 'currency_id')
    def _onchange_amount(self):
        res = {}
        journal_ids = []
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types))]
        if self.session_id and self.journal_ids:
            if self.payment_type == 'transfer':
                res['domain'] = {'journal_id': [('id', 'in', journal_ids)], 'destination_journal_id': [
                    ('id', 'in', journal_ids)]}
            else:
                res['domain'] = {'journal_id': [('id', 'in', journal_ids)]}
            return res
        if self.journal_id.type not in journal_types:
            self.journal_id = self.env['account.journal'].search(
                domain_on_types, limit=1)
            return {'domain': {'journal_id': jrnl_filters['domain'] + domain_on_types}}

    @api.model
    def default_get(self, fields):
        rec = super(Payment, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        rec.update({
            'journal_id': False,
            'invoice_number': ' '.join([ref for ref in invoices.mapped('move_name') if ref]),
        })
        return rec


Payment()
