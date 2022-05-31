# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from datetime import timedelta
from odoo.tools import float_is_zero


class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"

    filter_branch = True

    @api.model
    def _get_options_domain(self, options):
        domain = super(report_account_general_ledger, self)._get_options_domain(options)
        if options.get('branch') and options.get('branch_ids'):
            domain += [('branch_id', 'in', options.get('branch_ids'))]
        return domain

    @api.model
    def _get_columns_name(self, options):
        columns_names = [
            {'name': ''},
            {'name': _('Date'), 'class': 'date'},
            {'name': _('Communication')},
            {'name': _('Partner')},
            {'name': _('Branch'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'},
            {'name': _('Balance'), 'class': 'number'},
            {'name': _('VESTCD'), 'class': 'number'},
            {'name': _('DAGB'), 'class': 'number'},
            {'name': _('STUKNR'), 'class': 'number'},
            {'name': _('REGNR'), 'class': 'number'},
            {'name': _('BOEKJR'), 'class': 'number'},
            {'name': _('PER'), 'class': 'number'},
            {'name': _('DAG'), 'class': 'number'},
            {'name': _('MND'), 'class': 'number'},
            {'name': _('JAAR'), 'class': 'number'},
            {'name': _('GROOTB'), 'class': 'number'},
            {'name': _('KSTNPL"'), 'class': 'number'},
            {'name': _('FAKTNR'), 'class': 'number'},
            {'name': _('PNRR'), 'class': 'number'},
            {'name': _('OMSCHR'), 'class': 'number'},
            {'name': _('CONTROLLE'), 'class': 'number'},
            {'name': _('CURCD'), 'class': 'number'},
            {'name': _('BEDRAG'), 'class': 'number'},
            {'name': _('BEDRSRD'), 'class': 'number'},
            {'name': _('BEDRUSD"'), 'class': 'number'},
            {'name': _('OPERCDE'), 'class': 'number'},
            {'name': _('VLNR'), 'class': 'number'},
            {'name': _('GALLON'), 'class': 'number'},
            {'name': _('PLCDE'), 'class': 'number'},
            {'name': _('HANDL'), 'class': 'number'},
            {'name': _('MAALT'), 'class': 'number'},
            {'name': _('PAX'), 'class': 'number'},
            {'name': _('MANDGN'), 'class': 'number'},
            {'name': _('SDATUM'), 'class': 'number'},
            {'name': _('KSTNPL6'), 'class': 'number'},
            {'name': _('KSTNPL7'), 'class': 'number'},
            {'name': _('PERSNR'), 'class': 'number'},
            {'name': _('PONR'), 'class': 'number'},
            {'name': _('GALPRIJS'), 'class': 'number'},
            {'name': _('BETREKDG'), 'class': 'number'},
            {'name': _('BETREKMD'), 'class': 'number'},
            {'name': _('BETREKJR"'), 'class': 'number'},
            {'name': _('FACTDG'), 'class': 'number'},
            {'name': _('FACTMD'), 'class': 'number'},
            {'name': _('FACTJR'), 'class': 'number'},
            {'name': _('VLTYPE'), 'class': 'number'},
            {'name': _('VLTREG'), 'class': 'number'},
            {'name': _('CRED'), 'class': 'number'},
            {'name': _('DE'), 'class': 'number'}
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns_names.insert(4, {'name': _('Currency'), 'class': 'number'})
        return columns_names

    @api.model
    def _get_aml_line(self, options, account, aml, cumulated_balance):
        print (">>options>>", options)
        print (">>account>>", account)
        print (">>aml>>", aml)
        print (":::::0cumulated_balance,0", cumulated_balance)
        if aml['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move'

        if (aml['currency_id'] and aml['currency_id'] != account.company_id.currency_id.id) or account.currency_id:
            currency = self.env['res.currency'].browse(aml['currency_id'])
        else:
            currency = False

        aml_id = self.env['account.move.line'].browse(int(aml['id']))
        branch_id = aml_id.branch_id.name or ''
        columns = [
            {'name': format_date(self.env, aml['date']), 'class': 'date'},
            {'name': self._format_aml_name(aml['name'], aml['ref']), 'class': 'o_account_report_line_ellipsis'},
            {'name': aml['partner_name'], 'class': 'o_account_report_line_ellipsis'},
            {'name': branch_id, 'class': 'o_account_report_line_ellipsis', 'class': 'number'},
            {'name': self.format_value(aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['credit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(aml['vestcd']), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'},
            {'name': self.format_value(cumulated_balance), 'class': 'number'}
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(3, {'name': currency and aml['amount_currency'] and self.format_value(
                aml['amount_currency'], currency=currency, blank_if_zero=True) or '', 'class': 'number'})
        return {
            'id': aml['id'],
            'caret_options': caret_type,
            'parent_id': 'account_%d' % aml['account_id'],
            'name': aml['move_name'],
            'columns': columns,
            'level': 2,
        }

    @api.model
    def _get_initial_balance_line(self, options, account, amount_currency, debit, credit, balance):
        columns = [
            {'name': ''},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]

        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': has_foreign_currency and self.format_value(
                amount_currency, currency=account.currency_id, blank_if_zero=True) or '', 'class': 'number'})
        return {
            'id': 'initial_%d' % account.id,
            'class': 'o_account_reports_initial_balance',
            'name': _('Initial Balance'),
            'parent_id': 'account_%d' % account.id,
            'columns': columns,
            'colspan': 4,
        }

    @api.model
    def _get_account_total_line(self, options, account, amount_currency, debit, credit, balance):
        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False

        columns = []
        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': has_foreign_currency and self.format_value(
                amount_currency, currency=account.currency_id, blank_if_zero=True) or '', 'class': 'number'})

        columns += [
            {'name': ''},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]

        return {
            'id': 'total_%s' % account.id,
            'class': 'o_account_reports_domain_total',
            'parent_id': 'account_%s' % account.id,
            'name': _('Total %s', account["display_name"]),
            'columns': columns,
            'colspan': 4,
        }

    @api.model
    def _get_account_title_line(self, options, account, amount_currency, debit, credit, balance, has_lines):
        has_foreign_currency = account.currency_id and account.currency_id != account.company_id.currency_id or False
        unfold_all = self._context.get(
            'print_mode') and not options.get('unfolded_lines')

        name = '%s %s' % (account.code, account.name)
        columns = [
            {'name': ''},
            {'name': self.format_value(debit), 'class': 'number'},
            {'name': self.format_value(credit), 'class': 'number'},
            {'name': self.format_value(balance), 'class': 'number'},
        ]
        if self.user_has_groups('base.group_multi_currency'):
            columns.insert(0, {'name': has_foreign_currency and self.format_value(
                amount_currency, currency=account.currency_id, blank_if_zero=True) or '', 'class': 'number'})
        return {
            'id': 'account_%d' % account.id,
            'name': name,
            'columns': columns,
            'level': 1,
            'unfoldable': has_lines,
            'unfolded': has_lines and 'account_%d' % account.id in options.get('unfolded_lines') or unfold_all,
            'colspan': 4,
            'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
        }

    @api.model
    def _get_total_line(self, options, debit, credit, balance):
        return {
            'id': 'general_ledger_total_%s' % self.env.company.id,
            'name': _('Total'),
            'class': 'total',
            'level': 1,
            'columns': [
                {'name': ''},
                {'name': self.format_value(debit), 'class': 'number'},
                {'name': self.format_value(credit), 'class': 'number'},
                {'name': self.format_value(balance), 'class': 'number'},
            ],
            'colspan': self.user_has_groups('base.group_multi_currency') and 5 or 4,
        }


    @api.model
    def _get_query_amls(self, options, expanded_account, offset=None, limit=None):
        ''' Construct a query retrieving the account.move.lines when expanding a report line with or without the load
        more.
        :param options:             The report options.
        :param expanded_account:    The account.account record corresponding to the expanded line.
        :param offset:              The offset of the query (used by the load more).
        :param limit:               The limit of the query (used by the load more).
        :return:                    (query, params)
        '''

        unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:]) for line in options['unfolded_lines']])]

        new_options = self._force_strict_range(options)
        tables, where_clause, where_params = self._query_get(new_options, domain=domain)
        ct_query = self.env['res.currency']._get_query_currency_table(options)
        query = f'''
            SELECT
                account_move_line.id,
                account_move_line.date,
                account_move_line.date_maturity,
                account_move_line.name,
                account_move_line.ref,
                account_move_line.company_id,
                account_move_line.account_id,
                account_move_line.payment_id,
                account_move_line.partner_id,
                account_move_line.currency_id,
                account_move_line.amount_currency,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                account_move_line__move_id.move_type    AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name,
                account_move_line.vestcd                AS VESTCD
            FROM {tables}
            LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            WHERE {where_clause}
            ORDER BY account_move_line.date, account_move_line.id
        '''

        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params

    # @api.model
    # def _get_tax_declaration_lines(self, options, journal_type, taxes_results):
    #     lines = [{
    #         'id': 0,
    #         'name': _('Tax Declaration'),
    #         'columns': [{'name': v} for v in ['', '', '', '', '', '', '', '']],
    #         'level': 1,
    #         'unfoldable': False,
    #         'unfolded': False,
    #     }, {
    #         'id': 0,
    #         'name': _('Name'),
    #         'columns': [{'name': v} for v in ['', '', '', '', '', _('Base Amount'), _('Tax Amount'), '']],
    #         'level': 2,
    #         'unfoldable': False,
    #         'unfolded': False,
    #     }]
    #     for tax, results in taxes_results:
    #         sign = journal_type == 'sale' and -1 or 1
    #         base_amount = sign * results.get('base_amount', 0.0)
    #         tax_amount = sign * results.get('tax_amount', 0.0)
    #         lines.append({
    #             'id': '%s_tax' % tax.id,
    #             'name': '%s (%s)' % (tax.name, tax.amount),
    #             'caret_options': 'account.tax',
    #             'unfoldable': False,
    #             'columns': [{'name': v} for v in ['', '', '', '', '', self.format_value(base_amount), self.format_value(tax_amount), '']],
    #             'level': 4,
    #         })
    #     return lines
