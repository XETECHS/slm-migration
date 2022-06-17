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
        domain = super(report_account_general_ledger,
                       self)._get_options_domain(options)
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
            {'name': self._format_aml_name(
                aml['name'], aml['ref']), 'class': 'o_account_report_line_ellipsis'},
            {'name': aml['partner_name'],
                'class': 'o_account_report_line_ellipsis'},
            {'name': branch_id, 'class': 'o_account_report_line_ellipsis',
                'class': 'number'},
            {'name': self.format_value(
                aml['debit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(
                aml['credit'], blank_if_zero=True), 'class': 'number'},
            {'name': self.format_value(
                aml['balance'], blank_if_zero=True), 'class': 'number'},
            {'name': aml['vestcd'] if aml['vestcd'] != None else 0, 'class': 'number'},
            {'name': aml['dagb'] if aml['dagb'] != None else 0, 'class': 'number'},
            {'name': aml['stuknr'] if aml['stuknr'] != None else '', 'class': 'number'},
            {'name': aml['regnr'] if aml['regnr'] != None else '', 'class': 'number'},
            {'name': aml['boekjr'] if aml['boekjr'] != None else 0, 'class': 'number'},
            {'name': aml['per'] if aml['per'] != None else 0, 'class': 'number'},
            {'name': aml['dag'] if aml['dag'] != None else 0, 'class': 'number'},
            {'name': aml['mnd'] if aml['mnd'] != None else 0, 'class': 'number'},
            {'name': aml['jaar'] if aml['jaar'] != None else 0, 'class': 'number'},
            {'name': '', 'class': 'number'},  # GROOTB
            {'name': '', 'class': 'number'},  # KSTNPL
            {'name': aml['faktnr'] if aml['faktnr'] != None else '', 'class': 'number'},
            {'name': aml['pnrr'] if aml['pnrr'] != None else '', 'class': 'number'},
            {'name': aml['omschr'] if aml['omschr'] != None else '', 'class': 'number'},
            {'name': aml['controlle'] if aml['controlle'] != None else '', 'class': 'number'},
            {'name': aml['curcd'] if aml['curcd'] != None else 0, 'class': 'number'},
            {'name': aml['bedrag'] if aml['bedrag'] != None else 0.0, 'class': 'number'},
            {'name': aml['bedrsrd'] if aml['bedrsrd'] != None else 0.0, 'class': 'number'},
            {'name': aml['bedrusd'] if aml['bedrusd'] != None else 0.0, 'class': 'number'},
            {'name': aml['opercde'] if aml['opercde'] != None else 0, 'class': 'number'},
            {'name': aml['flight_name'], 'class': 'o_account_report_line_ellipsis'},  # VLNR
            {'name': aml['gallon'] if aml['gallon'] != None else 0.0, 'class': 'number'},
            {'name': aml['plcde'] if aml['plcde'] != None else '', 'class': 'number'},
            {'name': aml['handl'] if aml['handl'] != None else '', 'class': 'number'},
            {'name': aml['maalt'] if aml['maalt'] != None else '', 'class': 'number'},
            {'name': aml['pax'] if aml['pax'] != None else 0, 'class': 'number'},
            {'name': aml['mandgn'] if aml['mandgn'] != None else 0, 'class': 'number'},
            {'name': aml['sdatum'] if aml['sdatum'] != None else 0, 'class': 'number'},
            {'name': aml['kstnpl6'], 'class': 'o_account_report_line_ellipsis'},  # KSTNPL6
            {'name': aml['kstnpl7'], 'class': 'o_account_report_line_ellipsis'},  # KSTNPL7
            {'name': aml['persnr'] if aml['persnr'] != None else 0, 'class': 'number'},
            {'name': aml['ponr'] if aml['ponr'] != None else 0, 'class': 'number'},
            {'name': aml['galprijs'] if aml['galprijs'] != None else 0.0, 'class': 'number'},
            {'name': aml['betrekdg'] if aml['betrekdg'] != None else 0, 'class': 'number'},
            {'name': aml['betrekmd'] if aml['betrekmd'] != None else 0, 'class': 'number'},
            {'name': aml['betrekjr'] if aml['betrekjr'] != None else 0, 'class': 'number'},
            {'name': aml['factdg'] if aml['factdg'] != None else 0, 'class': 'number'},
            {'name': aml['factmd'] if aml['factmd'] != None else 0, 'class': 'number'},
            {'name': aml['factjr'] if aml['factjr'] != None else 0, 'class': 'number'},
            {'name': aml['vltype'] if aml['vltype'] != None else '', 'class': 'number'},
            {'name': aml['vltreg'] if aml['vltreg'] != None else '', 'class': 'number'},
            {'name': '', 'class': 'number'},  # CRED
            {'name': '', 'class': 'number'},  # DE
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
    def _get_general_ledger_lines(self, options, line_id=None):
        ''' Get lines for the whole report or for a specific line.
        :param options: The report options.
        :return:        A list of lines, each one represented by a dictionary.
        '''
        lines = []
        aml_lines = []
        options_list = self._get_options_periods_list(options)
        unfold_all = options.get('unfold_all') or (
            self._context.get('print_mode') and not options['unfolded_lines'])
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        expanded_account = line_id and self.env['account.account'].browse(
            int(line_id[8:]))
        accounts_results, taxes_results = self._do_query(
            options_list, expanded_account=expanded_account)

        total_debit = total_credit = total_balance = 0.0
        for account, periods_results in accounts_results:
            # No comparison allowed in the General Ledger. Then, take only the first period.
            results = periods_results[0]

            is_unfolded = 'account_%s' % account.id in options['unfolded_lines']

            # account.account record line.
            account_sum = results.get('sum', {})
            account_lines = results.get('lines', {})
            account_un_earn = results.get('unaffected_earnings', {})
            # Check if there is sub-lines for the current period.
            max_date = account_sum.get('max_date')
            has_lines = max_date and max_date >= date_from or False
            # print(account_lines)
            amount_currency = account_sum.get(
                'amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0)
            debit = account_sum.get('debit', 0.0) + \
                account_un_earn.get('debit', 0.0)
            credit = account_sum.get('credit', 0.0) + \
                account_un_earn.get('credit', 0.0)
            balance = account_sum.get(
                'balance', 0.0) + account_un_earn.get('balance', 0.0)
            vestcd = sum(al.get('vestcd', 0.0)
                         if al['vestcd'] != None else 0.0 for al in account_lines)
            dagb = sum(al.get('dagb', 0.0)
                       if al['dagb'] != None else 0.0 for al in account_lines)
            boekjr = sum(al.get('boekjr', 0.0)
                         if al['boekjr'] != None else 0.0 for al in account_lines)
            per = sum(al.get('per', 0.0)
                      if al['per'] != None else 0.0 for al in account_lines)
            dag = sum(al.get('dag', 0.0)
                      if al['dag'] != None else 0.0 for al in account_lines)
            mnd = sum(al.get('mnd', 0.0)
                      if al['mnd'] != None else 0.0 for al in account_lines)
            jaar = sum(al.get('jaar', 0.0)
                       if al['jaar'] != None else 0.0 for al in account_lines)
            curcd = sum(al.get('curcd', 0.0)
                        if al['curcd'] != None else 0.0 for al in account_lines)
            bedrag = sum(al.get('bedrag', 0.0)
                         if al['bedrag'] != None else 0.0 for al in account_lines)
            bedrsrd = sum(al.get('bedrsrd', 0.0)
                          if al['bedrsrd'] != None else 0.0 for al in account_lines)
            bedrusd = sum(al.get('bedrusd', 0.0)
                          if al['bedrusd'] != None else 0.0 for al in account_lines)
            opercde = sum(al.get('opercde', 0.0)
                          if al['opercde'] != None else 0.0 for al in account_lines)
            gallon = sum(al.get('gallon', 0.0)
                         if al['gallon'] != None else 0.0 for al in account_lines)
            pax = sum(al.get('pax', 0.0)
                      if al['pax'] != None else 0.0 for al in account_lines)
            mandgn = sum(al.get('mandgn', 0.0)
                         if al['mandgn'] != None else 0.0 for al in account_lines)
            sdatum = sum(al.get('sdatum', 0.0)
                         if al['sdatum'] != None else 0.0 for al in account_lines)
            persnr = sum(al.get('persnr', 0.0)
                         if al['persnr'] != None else 0.0 for al in account_lines)
            ponr = sum(al.get('ponr', 0.0)
                       if al['ponr'] != None else 0.0 for al in account_lines)
            galprijs = sum(al.get(
                'galprijs', 0.0) if al['galprijs'] != None else 0.0 for al in account_lines)
            betrekdg = sum(al.get(
                'betrekdg', 0.0) if al['betrekdg'] != None else 0.0 for al in account_lines)
            betrekmd = sum(al.get(
                'betrekmd', 0.0) if al['betrekmd'] != None else 0.0 for al in account_lines)
            betrekjr = sum(al.get(
                'betrekjr', 0.0) if al['betrekjr'] != None else 0.0 for al in account_lines)
            factdg = sum(al.get('factdg', 0.0)
                         if al['factdg'] != None else 0.0 for al in account_lines)
            factmd = sum(al.get('factmd', 0.0)
                         if al['factmd'] != None else 0.0 for al in account_lines)
            factjr = sum(al.get('factjr', 0.0)
                         if al['factjr'] != None else 0.0 for al in account_lines)
            title_line = self._get_account_title_line(
                options, account, amount_currency, debit, credit, balance, has_lines)
            extra_fields_list = [{'name': vestcd, 'class': 'number'}, {'name': dagb, 'class': 'number'}, {'name': ''}, {'name': ''}, {'name': boekjr, 'class': 'number'}, {'name': per, 'class': 'number'}, {'name': dag, 'class': 'number'},
                                 {'name': mnd, 'class': 'number'}, {'name': jaar, 'class': 'number'}, {'name': ''}, {'name': ''}, {
                                     'name': ''}, {'name': ''}, {'name': ''}, {'name': ''}, {'name': curcd, 'class': 'number'},
                                 {'name': bedrag, 'class': 'number'}, {'name': bedrsrd, 'class': 'number'}, {'name': bedrusd, 'class': 'number'}, {
                                     'name': opercde, 'class': 'number'}, {'name': ''}, {'name': gallon, 'class': 'number'},
                                 {'name': ''}, {'name': ''}, {'name': ''}, {'name': pax, 'class': 'number'}, {
                                     'name': mandgn, 'class': 'number'}, {'name': sdatum, 'class': 'number'}, {'name': ''}, {'name': ''},
                                 {'name': persnr, 'class': 'number'}, {'name': ponr, 'class': 'number'}, {'name': galprijs, 'class': 'number'}, {
                                     'name': betrekdg, 'class': 'number'}, {'name': betrekmd, 'class': 'number'},
                                 {'name': betrekjr, 'class': 'number'}, {'name': factdg, 'class': 'number'}, {'name': factmd, 'class': 'number'}, {'name': factjr, 'class': 'number'}, ]
            title_line['columns'] += extra_fields_list
            lines.append(title_line)
            total_debit += debit
            total_credit += credit
            total_balance += balance
            # self.MAX_LINES = 1000
            if has_lines and (unfold_all or is_unfolded):
                # Initial balance line.
                account_init_bal = results.get('initial_balance', {})

                cumulated_balance = account_init_bal.get(
                    'balance', 0.0) + account_un_earn.get('balance', 0.0)

                lines.append(self._get_initial_balance_line(
                    options, account,
                    account_init_bal.get(
                        'amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    account_init_bal.get('debit', 0.0) +
                    account_un_earn.get('debit', 0.0),
                    account_init_bal.get('credit', 0.0) +
                    account_un_earn.get('credit', 0.0),
                    cumulated_balance,
                ))

                # account.move.line record lines.
                amls = results.get('lines', [])

                load_more_remaining = len(amls)
                load_more_counter = self._context.get(
                    'print_mode') and load_more_remaining or self.MAX_LINES

                for aml in amls:
                    # Don't show more line than load_more_counter.
                    if load_more_counter == 0:
                        break

                    cumulated_balance += aml['balance']
                    lines.append(self._get_aml_line(
                        options, account, aml, company_currency.round(cumulated_balance)))

                    load_more_remaining -= 1
                    load_more_counter -= 1
                    aml_lines.append(aml['id'])

                if load_more_remaining > 0:
                    # Load more line.
                    lines.append(self._get_load_more_line(
                        options, account,
                        self.MAX_LINES,
                        load_more_remaining,
                        cumulated_balance,
                    ))

                if self.env.company.totals_below_sections:
                    # Account total line.
                    lines.append(self._get_account_total_line(
                        options, account,
                        account_sum.get('amount_currency', 0.0),
                        account_sum.get('debit', 0.0),
                        account_sum.get('credit', 0.0),
                        account_sum.get('balance', 0.0),
                    ))

        if not line_id:
            # Report total line.
            lines.append(self._get_total_line(
                options,
                total_debit,
                total_credit,
                company_currency.round(total_balance),
            ))

            # Tax Declaration lines.
            journal_options = self._get_options_journals(options)
            if len(journal_options) == 1 and journal_options[0]['type'] in ('sale', 'purchase'):
                lines += self._get_tax_declaration_lines(
                    options, journal_options[0]['type'], taxes_results
                )
        if self.env.context.get('aml_only'):
            return aml_lines
        return lines

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

        unfold_all = options.get('unfold_all') or (
            self._context.get('print_mode') and not options['unfolded_lines'])

        # Get sums for the account move lines.
        # period: [('date' <= options['date_to']), ('date', '>=', options['date_from'])]
        if expanded_account:
            domain = [('account_id', '=', expanded_account.id)]
        elif unfold_all:
            domain = []
        elif options['unfolded_lines']:
            domain = [('account_id', 'in', [int(line[8:])
                                            for line in options['unfolded_lines']])]

        new_options = self._force_strict_range(options)
        tables, where_clause, where_params = self._query_get(
            new_options, domain=domain)
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
                account_move_line.vlnr,
                account_move_line.kstnpl6,
                account_move_line.kstnpl7,
                account_move_line.amount_currency,
                ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                account_move_line__move_id.name         AS move_name,
                company.currency_id                     AS company_currency_id,
                partner.name                            AS partner_name,
                flight.name                            AS flight_name,
                anly_acc6.name                            AS kstnpl6,
                anly_acc7.name                            AS kstnpl7,
                account_move_line__move_id.move_type    AS move_type,
                account.code                            AS account_code,
                account.name                            AS account_name,
                journal.code                            AS journal_code,
                journal.name                            AS journal_name,
                full_rec.name                           AS full_rec_name,
                account_move_line.vestcd AS VESTCD,
                account_move_line.dagb AS DAGB,
                account_move_line.stuknr AS STUKNR,
                account_move_line.regnr AS REGNR,
                account_move_line.boekjr AS BOEKJR,
                account_move_line.per AS PER,
                account_move_line.dag AS DAG,
                account_move_line.mnd AS MND,
                account_move_line.jaar AS JAAR,
                account_move_line.faktnr AS FAKTNR,
                account_move_line.pnr AS PNRR,
                account_move_line.omschr AS OMSCHR,
                account_move_line.controlle AS CONTROLLE,
                account_move_line.curcd AS CURCD,
                account_move_line.bedrag AS BEDRAG,
                account_move_line.bedrsrd AS BEDRSRD,
                account_move_line.bedrusd AS BEDRUSD,
                account_move_line.opercde AS OPERCDE,
                account_move_line.gallon AS GALLON,
                account_move_line.plcde AS PLCDE,
                account_move_line.handl AS HANDL,
                account_move_line.maalt AS MAALT,
                account_move_line.pax AS PAX,
                account_move_line.mandgn AS MANDGN,
                account_move_line.sdatum AS SDATUM,
                account_move_line.persnr AS PERSNR,
                account_move_line.ponr AS PONR,
                account_move_line.galprijs AS GALPRIJS,
                account_move_line.betrekdg AS BETREKDG,
                account_move_line.betrekmd AS BETREKMD,
                account_move_line.betrekjr AS BETREKJR,
                account_move_line.factdg AS FACTDG,
                account_move_line.factmd AS FACTMD,
                account_move_line.factjr AS FACTJR,
                account_move_line.vltype AS VLTYPE,
                account_move_line.vltreg AS VLTREG

            FROM {tables}
            LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
            LEFT JOIN res_company company               ON company.id = account_move_line.company_id
            LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
            LEFT JOIN flight_list flight               ON flight.id = account_move_line.vlnr
            LEFT JOIN account_account account           ON account.id = account_move_line.account_id
            LEFT JOIN account_analytic_account anly_acc6  ON anly_acc6.id = account_move_line.kstnpl6
            LEFT JOIN account_analytic_account anly_acc7  ON anly_acc7.id = account_move_line.kstnpl7
            LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
            LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
            WHERE {where_clause}
            ORDER BY account_move_line.date, account_move_line.id'''
        if offset:
            query += ' OFFSET %s '
            where_params.append(offset)
        if limit:
            query += ' LIMIT %s '
            where_params.append(limit)

        return query, where_params
