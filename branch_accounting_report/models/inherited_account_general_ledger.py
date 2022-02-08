# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from datetime import timedelta
from odoo.tools import float_is_zero
import re
from datetime import datetime


class report_account_general_ledger(models.AbstractModel):
    _inherit = "account.general.ledger"

    filter_vlnr = True

    def _set_context(self, options):
        ctx = super(report_account_general_ledger, self)._set_context(options)

        numbers = []
        if options.get('vlnr'):
            numbers = [c.get('id') for c in options['vlnr'] if c.get('selected')]
            numbers = numbers if len(numbers) > 0 else []
        ctx['numbers'] = len(numbers) > 0 and numbers
        return ctx

    def _get_options_vlnr(self):
        numbers = self.env['flight.list'].search([], order="name")
        return [{'id': c.id, 'name': c.name, 'selected': False} for c in numbers]

    def _build_options(self, previous_options=None):
        if not previous_options:
            previous_options = {}
        options = super(report_account_general_ledger, self)._build_options(previous_options)
        if options.get('vlnr'):
            options['vlnr'] = self._get_options_vlnr()
        # Merge old options with default from this report
        for key, value in options.items():
            if key in previous_options and value is not None and previous_options[key] is not None:
                if key == 'vlnr':
                    for index, vlnr in enumerate(options[key]):
                        selected_vlnr = next((previous_option for previous_option in previous_options[key]
                                              if previous_option['id'] == vlnr['id']), None)
                        if selected_vlnr:
                            options[key][index] = selected_vlnr
        return options

    def _do_query(self, options, line_id, group_by_account=True, limit=False):
        context = self.env.context
        numbers = context.get('numbers', None)
        if group_by_account:
            select = "SELECT \"account_move_line\".account_id"
            if self.env.user.company_id.currency_id.id != 2:
                select += """
                    ,COALESCE(
                        SUM(
                            "account_move_line".debit
                            -"account_move_line".credit
                        ), 
                        0
                    ),
                    SUM("account_move_line".amount_currency),
                    COALESCE(
                        SUM("account_move_line".debit),
                         0
                     ),
                     COALESCE(        
                         SUM("account_move_line".credit),
                         0
                     )
                     """
            else:
                select += """
                   ,COALESCE(
                       SUM(
                           "account_move_line".debit /
                               (CASE WHEN "account_move_line".company_currency_id = 2 THEN 1 ELSE "res_currency_rate".rate END)
                           -"account_move_line".credit /
                               (CASE WHEN "account_move_line".company_currency_id = 2 THEN 1 ELSE "res_currency_rate".rate END)
                       ), 
                       0
                   ),
                   SUM("account_move_line".amount_currency),
                   COALESCE(
                       SUM("account_move_line".debit / 
                           (CASE WHEN "account_move_line".company_currency_id = 2 THEN 1 ELSE "res_currency_rate".rate END)),
                        0
                    ),
                    COALESCE(        
                        SUM("account_move_line".credit / 
                            (CASE WHEN "account_move_line".company_currency_id = 2 THEN 1 ELSE "res_currency_rate".rate END)),
                        0
                    )
                    """
            if options.get('cash_basis'):
                select = select.replace('debit', 'debit_cash_basis').replace('credit', 'credit_cash_basis')
        else:
            select = "SELECT \"account_move_line\".id"
        sql = "%s FROM %s "
        if self.env.user.company_id.currency_id.id == 2:
            join = """LEFT JOIN "res_currency_rate" ON 
                                ("account_move_line".company_currency_id = "res_currency_rate".currency_id 
                                    AND "res_currency_rate".name = date_trunc('month', "account_move_line".date)::date) """
        else:
            join = ""

        if numbers:
            join_vlnr = """ JOIN flight_list ON ("account_move_line".vlnr = "flight_list".id) """
        else:
            join_vlnr = ""

        where = "WHERE %s%s"
        sql += join + join_vlnr + where
        if group_by_account:
            sql += "GROUP BY \"account_move_line\".account_id"
        else:
            sql += " GROUP BY \"account_move_line\".id"
            sql += " ORDER BY MAX(\"account_move_line\".date),\"account_move_line\".id"
            if limit and isinstance(limit, int):
                sql += " LIMIT " + str(limit)
        user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))])
        with_sql, with_params = self._get_with_statement(user_types)
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        line_clause = line_id and ' AND \"account_move_line\".account_id = ' + str(line_id) or ''
        if options.get('branch'):
            where_clause += 'and ("account_move_line"."branch_id" in ('
            for a in range(len(options.get('branch'))):
                where_clause += '%s,'
            where_clause = where_clause[:-1]

            where_clause += '))'
            # branch_list = [1,2]
            for a in options.get('branch'):
                where_params.append(int(a))
        if numbers:
            where_args = ['%s' for number in numbers]
            where_clause += ' AND "flight_list".id in ({})'.format(','.join(where_args))
            for a in numbers:
                where_params.append(int(a))
        query = sql % (select, tables, where_clause, line_clause)
        self.env.cr.execute(with_sql + query, with_params + where_params)
        results = self.env.cr.fetchall()
        return results

    def _group_by_account_id(self, options, line_id):
        accounts = {}
        results = self._do_query_group_by_account(options, line_id)
        initial_bal_date_to = fields.Date.from_string(self.env.context['date_from_aml']) + timedelta(days=-1)
        initial_bal_results = self.with_context(
            date_to=initial_bal_date_to.strftime('%Y-%m-%d'))._do_query_group_by_account(options, line_id)

        context = self.env.context

        last_day_previous_fy = \
        self.env.user.company_id.compute_fiscalyear_dates(fields.Date.from_string(self.env.context['date_from_aml']))[
            'date_from'] + timedelta(days=-1)
        unaffected_earnings_per_company = {}
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            unaffected_earnings_per_company[company] = self.with_context(
                date_to=last_day_previous_fy.strftime('%Y-%m-%d'), date_from=False)._do_query_unaffected_earnings(
                options, line_id, company)

        unaff_earnings_treated_companies = set()
        unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
        for account_id, result in results.items():
            account = self.env['account.account'].browse(account_id)
            accounts[account] = result
            accounts[account]['initial_bal'] = initial_bal_results.get(account.id,
                                                                       {'balance': 0, 'amount_currency': 0, 'debit': 0,
                                                                        'credit': 0})
            if account.user_type_id == unaffected_earnings_type and account.company_id not in unaff_earnings_treated_companies:
                # add the benefit/loss of previous fiscal year to unaffected earnings accounts
                unaffected_earnings_results = unaffected_earnings_per_company[account.company_id]
                for field in ['balance', 'debit', 'credit']:
                    accounts[account]['initial_bal'][field] += unaffected_earnings_results[field]
                    accounts[account][field] += unaffected_earnings_results[field]
                unaff_earnings_treated_companies.add(account.company_id)
            # use query_get + with statement instead of a search in order to work in cash basis too
            aml_ctx = {}
            if context.get('date_from_aml'):
                aml_ctx = {
                    'strict_range': True,
                    'date_from': context['date_from_aml'],
                }
            aml_ids = self.with_context(**aml_ctx)._do_query(options, account_id, group_by_account=False)
            aml_ids = [x[0] for x in aml_ids]

            accounts[account]['total_lines'] = len(aml_ids)
            offset = int(options.get('lines_offset', 0))
            if self.MAX_LINES:
                stop = offset + self.MAX_LINES
            else:
                stop = None
            aml_ids = aml_ids[offset:stop]

            accounts[account]['lines'] = self.env['account.move.line'].browse(aml_ids)

        # For each company, if the unaffected earnings account wasn't in the selection yet: add it manually
        user_currency = self.env.user.company_id.currency_id
        for cid in context.get('company_ids', []):
            company = self.env['res.company'].browse(cid)
            if company not in unaff_earnings_treated_companies and not float_is_zero(
                    unaffected_earnings_per_company[company]['balance'], precision_digits=user_currency.decimal_places):
                unaffected_earnings_account = self.env['account.account'].search([
                    ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', '=', company.id)
                ], limit=1)
                if unaffected_earnings_account and (not line_id or unaffected_earnings_account.id == line_id):
                    accounts[unaffected_earnings_account[0]] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['initial_bal'] = unaffected_earnings_per_company[company]
                    accounts[unaffected_earnings_account[0]]['lines'] = []
        return accounts

    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        lines = []
        temp = []
        context = self.env.context
        company_id = self.env.user.company_id
        used_currency = company_id.currency_id
        dt_from = options['date'].get('date_from')
        line_id = line_id and int(line_id.split('_')[1]) or None
        aml_lines = []
        grouped_lines = []
        grouped_initial_lines = []
        grouped_folded_lines = []
        grouped_total_lines = []
        grouped_folded_total_lines = []
        end_grouped_initial_lines = False
        end_grouped_folded_lines = False
        end_grouped_total_lines = False
        end_grouped_folded_total_lines = False
        consolidating = False
        # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to
        # either the beginning of the fy or the beginning of times depending on the account
        grouped_accounts = self.with_context(date_from_aml=dt_from,
                                             date_from=dt_from and company_id.compute_fiscalyear_dates(
                                                 fields.Date.from_string(dt_from))[
                                                 'date_from'] or None)._group_by_account_id(options, line_id)

        if line_id:
            try:
                company_ids = [company['id'] for company in options['multi_company'] if company['selected']]
                account_obj = self.env['account.account'].search([('id', '=', line_id)], limit=1)
                code = account_obj.code
                others_accounts = self.env['account.account'].search([('code', '=', code), ('id', '!=', line_id),
                                                                      ('company_id', 'in', company_ids)])
                if others_accounts:
                    for account_obj in others_accounts:
                        grouped_other_accounts = self.with_context(date_from_aml=dt_from,
                                                                   date_from=dt_from and
                                                                             company_id.compute_fiscalyear_dates(
                                                                                 fields.Date.from_string(dt_from))[
                                                                                 'date_from'] or None)._group_by_account_id(
                            options, account_obj.id)
                        grouped_accounts.update(grouped_other_accounts)
            except KeyError:
                pass

        sorted_accounts = sorted(grouped_accounts, key=lambda a: int(re.sub("[^0-9]+", "", a.code)))
        # Reordering
        # First identify the first PL account (4XXXXXX account) and the 999999 account and any account after that 
        # are Balance accounts
        first_pl_account = None
        odoo_import_account = None
        balance_accounts_at_the_end = []
        sorted_accounts_filtered = sorted_accounts.copy()
        for account_obj in sorted_accounts:
            if not first_pl_account and account_obj.code[0] == '4':
                first_pl_account = account_obj
            elif account_obj.code == '999999':
                odoo_import_account = account_obj
                sorted_accounts_filtered.remove(account_obj)
            elif odoo_import_account:
                balance_accounts_at_the_end.append(account_obj)
                sorted_accounts_filtered.remove(account_obj)

        # # Add the odoo import account to the balance account at the end list
        if odoo_import_account:
            balance_accounts_at_the_end.append(odoo_import_account)
        # # Place the balance account removed before the PL accounts and the  999999 account
        for account_obj in balance_accounts_at_the_end:
            for i in range(len(sorted_accounts_filtered)):
                if sorted_accounts_filtered[i] == first_pl_account:
                    sorted_accounts_filtered.insert(i, account_obj)
                    break
        sorted_accounts = sorted_accounts_filtered

        unfold_all = options and 'unfold_all' in options and options['unfold_all']
        sum_debit = sum_credit = sum_balance = 0
        parent = {}
        total_balance = 0
        for account in sorted_accounts:
            display_name = account.code + " " + account.name
            if options.get('filter_accounts'):
                #  skip all accounts where both the code and the name don't start with the given filtering string
                if not any(
                        [display_name_part.lower().startswith(options['filter_accounts'].lower()) for display_name_part
                         in display_name.split(' ')]):
                    continue
            debit = grouped_accounts[account]['debit']
            credit = grouped_accounts[account]['credit']
            balance = grouped_accounts[account]['balance']
            sum_debit += debit
            sum_credit += credit
            sum_balance += balance
            amount_currency = '' if not account.currency_id else self.with_context(no_format=False).format_value(
                grouped_accounts[account]['amount_currency'], currency=account.currency_id)
            # don't add header for `load more`
            # print(display_name)
            if offset == 0:
                if len(grouped_lines) > 0:
                    if grouped_lines[-1]['name'] != display_name:
                        parent = {'account_id': account.id,
                                  'unfolded': 'account_%s' % (account.id,) in options.get('unfolded_lines')}
                        end_grouped_initial_lines = True
                        end_grouped_folded_lines = True
                        end_grouped_total_lines = True
                        end_grouped_folded_total_lines = True
                        # print('terminar agrupamiento')
                        if len(grouped_lines) > 1:
                            new_line = grouped_lines[0]
                            grouped_sum_amount_currency = 0.0
                            grouped_sum_debit = 0.0
                            grouped_sum_credit = 0.0
                            grouped_sum_balance = 0.0
                            for line in grouped_lines:
                                grouped_sum_amount_currency += line['raw_values'][0]
                                grouped_sum_debit += line['raw_values'][1]
                                grouped_sum_credit += line['raw_values'][2]
                                grouped_sum_balance += line['raw_values'][3]
                            new_line['columns'] = [{'name': v} for v in [
                                '' if grouped_sum_amount_currency == 0.0 else grouped_sum_amount_currency,
                                self.format_value(grouped_sum_debit), self.format_value(grouped_sum_credit),
                                self.format_value(grouped_sum_balance)]]
                            lines.append(new_line)
                            consolidating = True
                            # print('consolidating')
                        else:
                            lines.extend(grouped_lines)
                        grouped_lines = []
                elif len(grouped_lines) == 0:
                    parent = {'account_id': account.id,
                              'unfolded': 'account_%s' % (account.id,) in options.get('unfolded_lines')}
                grouped_lines.append({
                    'id': 'account_%s' % (parent['account_id'],),
                    'name': len(display_name) > 40 and not context.get('print_mode') and display_name[
                                                                                         :40] + '...' or display_name,
                    'title_hover': display_name,
                    'columns': [{'name': v} for v in
                                [amount_currency, self.format_value(debit), self.format_value(credit),
                                 self.format_value(balance)]],
                    'level': 2,
                    'unfoldable': True,
                    'unfolded': 'account_%s' % (parent['account_id'],) in options.get('unfolded_lines') or unfold_all,
                    'colspan': 4,
                    'raw_values': [0.0 if not account.currency_id else grouped_accounts[account]['amount_currency'],
                                   debit, credit, balance]
                })
            if 'account_%s' % (parent['account_id'],) in options.get('unfolded_lines') or unfold_all:
                # print('folded')
                initial_debit = grouped_accounts[account]['initial_bal']['debit']
                initial_credit = grouped_accounts[account]['initial_bal']['credit']
                initial_balance = grouped_accounts[account]['initial_bal']['balance']
                initial_currency = '' if not account.currency_id else self.with_context(no_format=False).format_value(
                    grouped_accounts[account]['initial_bal']['amount_currency'], currency=account.currency_id)

                domain_lines = []
                if offset == 0:
                    if end_grouped_initial_lines:
                        if len(grouped_initial_lines) > 1:
                            new_line = grouped_initial_lines[0]
                            grouped_sum_amount_currency = 0.0
                            grouped_sum_debit = 0.0
                            grouped_sum_credit = 0.0
                            grouped_sum_balance = 0.0
                            for line in grouped_initial_lines:
                                grouped_sum_amount_currency += line['raw_values'][0]
                                grouped_sum_debit += line['raw_values'][1]
                                grouped_sum_credit += line['raw_values'][2]
                                grouped_sum_balance += line['raw_values'][3]
                            new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                         '' if grouped_sum_amount_currency == 0.0 else grouped_sum_amount_currency,
                                                                         self.format_value(grouped_sum_debit),
                                                                         self.format_value(grouped_sum_credit),
                                                                         self.format_value(grouped_sum_balance)]]
                            # print('agregando el initial')
                            lines.append(new_line)
                        else:
                            lines.extend(grouped_initial_lines)
                        grouped_initial_lines = []
                        end_grouped_initial_lines = False

                    grouped_initial_lines.append({
                        'id': 'initial_%s' % (parent['account_id'],),
                        'class': 'o_account_reports_initial_balance',
                        'name': _('Initial Balance'),
                        'parent_id': 'account_%s' % (parent['account_id'],),
                        'columns': [{'name': v} for v in
                                    ['', '', '', initial_currency, self.format_value(initial_debit),
                                     self.format_value(initial_credit), self.format_value(initial_balance)]],
                        'raw_values': [0.0 if not account.currency_id else grouped_accounts[account]['initial_bal'][
                            'amount_currency'],
                                       initial_debit, initial_credit, initial_balance]
                    })
                    # print('lineas iniciales ', len(grouped_initial_lines))
                    progress = initial_balance
                else:
                    # for load more:
                    progress = float(options.get('lines_progress', initial_balance))

                amls = grouped_accounts[account]['lines']
                if options['branch']:
                    for a in amls:
                        if str(a.branch_id.id) in options['branch']:
                            temp.append(a)
                    amls = temp
                    amls = self.env['account.move.line'].browse([a.id for a in amls])
                remaining_lines = 0
                if not context.get('print_mode'):
                    remaining_lines = grouped_accounts[account]['total_lines'] - offset - len(amls)

                for line in amls:
                    # print('procesar detalles')
                    if options.get('cash_basis'):
                        line_debit = line.debit_cash_basis
                        line_credit = line.credit_cash_basis
                    else:
                        line_debit = line.debit
                        line_credit = line.credit

                    first_day_month_move = line.move_id.date.replace(day=1)
                    date = first_day_month_move or datetime.strptime(dt_from,
                                                                     '%Y-%m-%d').date() or self.env.context.get(
                        'date') or fields.Date.today()

                    line_debit = line.company_id.currency_id._convert(line_debit, used_currency, company_id, date)
                    line_credit = line.company_id.currency_id._convert(line_credit, used_currency, company_id, date)
                    progress = progress + line_debit - line_credit
                    currency = "" if not line.currency_id else self.with_context(no_format=False).format_value(
                        line.amount_currency, currency=line.currency_id)

                    name = line.name and line.name or ''
                    if line.ref:
                        name = name and name + ' - ' + line.ref or line.ref
                    name_title = name
                    # Don't split the name when printing
                    if len(name) > 35 and not self.env.context.get('no_format') and not self.env.context.get(
                            'print_mode'):
                        name = name[:32] + "..."
                    partner_name = line.partner_id.name
                    if isinstance(partner_name, str) and len(partner_name) > 20 and not self.env.context.get(
                            'no_format') and not self.env.context.get('print_mode'):
                        partner_name = partner_name[:20] + "..."
                    if line.invoice_id and line.invoice_id.number:
                        pnr = str(line.invoice_id.number)
                    elif line.payment_id and line.payment_id.invoice_number:
                        pnr = str(line.payment_id.invoice_number)
                    else:
                        pnr = line.pnr

                    partner_name_title = partner_name
                    if partner_name and len(partner_name) > 35 and not self.env.context.get(
                            'no_format') and not self.env.context.get('print_mode'):
                        partner_name = partner_name[:32] + "..."
                    caret_type = 'account.move'
                    if line.invoice_id:
                        caret_type = 'account.invoice.in' if line.invoice_id.type in (
                        'in_refund', 'in_invoice') else 'account.invoice.out'
                    elif line.payment_id:
                        caret_type = 'account.payment'

                    if line.vlnr:
                        vlnr = line.vlnr.name
                    else:
                        vlnr = None

                    if line.kstnpl6:
                        kstnpl6 = line.kstnpl6.code
                    else:
                        kstnpl6 = ''

                    if line.kstnpl7:
                        kstnpl7 = line.kstnpl7.code
                    else:
                        kstnpl7 = ''

                    columns = [{'name': v} for v in [format_date(self.env, line.date), name, partner_name, currency,
                                                     line_debit != 0 and self.format_value(line_debit) or '',
                                                     line_credit != 0 and self.format_value(line_credit) or '',
                                                     self.format_value(progress), line.vestcd, line.dagb, line.stuknr,
                                                     line.regnr, line.boekjr,
                                                     line.per, line.dag, line.mnd, line.jaar, line.account_id.code,
                                                     line.analytic_account_id.code, line.faktnr,
                                                     pnr, line.omschr, line.controlle, line.curcd, line.bedrag,
                                                     line.bedrsrd,
                                                     line.bedrusd, line.opercde, vlnr, line.gallon, line.plcde,
                                                     line.handl,
                                                     line.maalt, line.pax, line.mandgn, line.sdatum, kstnpl6, kstnpl7,
                                                     line.persnr, line.ponr, line.galprijs, line.betrekdg,
                                                     line.betrekmd, line.betrekjr,
                                                     line.factdg, line.factmd, line.factjr, line.vltype, line.vltreg]]
                    columns[1]['class'] = 'whitespace_print'
                    columns[2]['class'] = 'whitespace_print'
                    columns[1]['title'] = name_title
                    columns[2]['title'] = partner_name_title
                    line_value = {
                        'id': line.id,
                        'caret_options': caret_type,
                        'class': 'top-vertical-align',
                        'parent_id': 'account_%s' % (parent['account_id'],),
                        'name': line.move_id.name if line.move_id.name else '/',
                        'columns': columns,
                        'level': 4,
                    }
                    aml_lines.append(line.id)
                    if end_grouped_folded_lines:
                        # print('agregando detalles')
                        # print(len(grouped_folded_lines))
                        if context.get('print_mode'):
                            lines.extend(grouped_folded_lines)
                        else:
                            lines.extend(grouped_folded_lines[:2000])
                        grouped_folded_lines = []
                        end_grouped_folded_lines = False
                    grouped_folded_lines.append(line_value)

                if end_grouped_folded_lines:
                    # print('agregando detalles fuera del for')
                    # print(len(grouped_folded_lines))
                    if context.get('print_mode'):
                        lines.extend(grouped_folded_lines)
                    else:
                        lines.extend(grouped_folded_lines[:2000])
                    grouped_folded_lines = []
                    end_grouped_folded_lines = False

                # load more
                if remaining_lines > 0:
                    domain_lines.append({
                        'id': 'loadmore_%s' % account.id,
                        # if MAX_LINES is None, there will be no remaining lines
                        # so this should not cause a problem
                        'offset': offset + self.MAX_LINES,
                        'progress': progress,
                        'class': 'o_account_reports_load_more text-center',
                        'parent_id': 'account_%s' % (account.id,),
                        'name': _('Load more... (%s remaining)') % remaining_lines,
                        'colspan': 7,
                        'columns': [{}],
                    })
                # don't add total line for `load more`
                if offset == 0:
                    if end_grouped_folded_total_lines:
                        if len(grouped_folded_total_lines) > 1:
                            new_line = grouped_folded_total_lines[0]
                            grouped_sum_amount_currency = 0.0
                            grouped_sum_debit = 0.0
                            grouped_sum_credit = 0.0
                            grouped_sum_balance = 0.0
                            for line in grouped_folded_total_lines:
                                grouped_sum_amount_currency += line['raw_values'][0]
                                grouped_sum_debit += line['raw_values'][1]
                                grouped_sum_credit += line['raw_values'][2]
                                grouped_sum_balance += line['raw_values'][3]
                            formatted_grouped_sum_amount_currency = '' if not account.currency_id else self.with_context(
                                no_format=False).format_value(grouped_sum_amount_currency, currency=account.currency_id)
                            new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                         '' if grouped_sum_amount_currency == 0.0
                                                                         else formatted_grouped_sum_amount_currency,
                                                                         self.format_value(grouped_sum_debit),
                                                                         self.format_value(grouped_sum_credit),
                                                                         self.format_value(grouped_sum_balance)]]
                            # print('agregando el folded total del for')
                            lines.append(new_line)
                        else:
                            # print('agregando el folded total dentro del for')
                            lines.extend(grouped_folded_total_lines)
                        grouped_folded_total_lines = []
                        end_grouped_folded_total_lines = False

                    grouped_folded_total_lines.append({
                        'id': 'total_' + str(parent['account_id']),
                        'class': 'o_account_reports_domain_total',
                        'parent_id': 'account_%s' % (parent['account_id'],),
                        'name': _('Total '),
                        'columns': [{'name': v} for v in ['', '', '', amount_currency, self.format_value(debit),
                                                          self.format_value(credit), self.format_value(balance)]],
                        'raw_values': [0.0 if not account.currency_id else grouped_accounts[account]['amount_currency'],
                                       debit, credit, balance]
                    })

                # lines += domain_lines
            else:
                if end_grouped_initial_lines:
                    if len(grouped_initial_lines) > 1:
                        new_line = grouped_initial_lines[0]
                        grouped_sum_amount_currency = 0.0
                        grouped_sum_debit = 0.0
                        grouped_sum_credit = 0.0
                        grouped_sum_balance = 0.0
                        for line in grouped_initial_lines:
                            grouped_sum_amount_currency += line['raw_values'][0]
                            grouped_sum_debit += line['raw_values'][1]
                            grouped_sum_credit += line['raw_values'][2]
                            grouped_sum_balance += line['raw_values'][3]
                        new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                     '' if grouped_sum_amount_currency == 0.0 else grouped_sum_amount_currency,
                                                                     self.format_value(grouped_sum_debit),
                                                                     self.format_value(grouped_sum_credit),
                                                                     self.format_value(grouped_sum_balance)]]
                        lines.append(new_line)
                    else:
                        # print('agregando el initial')
                        lines.extend(grouped_initial_lines)
                    grouped_initial_lines = []
                    end_grouped_initial_lines = False

                    if len(grouped_folded_lines) > 0:
                        # print('agregando detalles')
                        # print(len(grouped_folded_lines))
                        if context.get('print_mode'):
                            lines.extend(grouped_folded_lines)
                        else:
                            lines.extend(grouped_folded_lines[:2000])
                    grouped_folded_lines = []

                    if len(grouped_folded_total_lines) > 1:
                        new_line = grouped_folded_total_lines[0]
                        grouped_sum_amount_currency = 0.0
                        grouped_sum_debit = 0.0
                        grouped_sum_credit = 0.0
                        grouped_sum_balance = 0.0
                        for line in grouped_folded_total_lines:
                            grouped_sum_amount_currency += line['raw_values'][0]
                            grouped_sum_debit += line['raw_values'][1]
                            grouped_sum_credit += line['raw_values'][2]
                            grouped_sum_balance += line['raw_values'][3]
                        formatted_grouped_sum_amount_currency = '' if not account.currency_id else self.with_context(
                            no_format=False).format_value(grouped_sum_amount_currency, currency=account.currency_id)
                        new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                     '' if grouped_sum_amount_currency == 0.0 else formatted_grouped_sum_amount_currency,
                                                                     self.format_value(grouped_sum_debit),
                                                                     self.format_value(grouped_sum_credit),
                                                                     self.format_value(grouped_sum_balance)]]
                        lines.append(new_line)
                        # print('agregando el folded total fuera del for')
                    else:
                        # print('agregando el folded total fuera del for')
                        lines.extend(grouped_folded_total_lines)
                    grouped_folded_total_lines = []

            if account == first_pl_account:
                lines.append({
                    'id': 'total_balance',
                    'name': 'Total Balance',
                    # 'title_hover': 'Total Balance',
                    'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': self.format_value(total_balance)}],
                    'level': 1,
                    'unfoldable': False,
                    'colspan': 4,
                    'style': 'font-size:15px'
                })
                total_balance = 0
            elif account == sorted_accounts[-1] and not line_id:
                total_balance += balance
                total_pl_line = {
                    'id': 'total_pl',
                    'name': 'Total Profit & Loss',
                    # 'title_hover': 'Total Balance',
                    'columns': [{'name': ''}, {'name': ''}, {'name': ''}, {'name': self.format_value(total_balance)}],
                    'level': 1,
                    'unfoldable': False,
                    'colspan': 4,
                    'style': 'font-size:15px'
                }
            total_balance += balance
        if not line_id and sorted_accounts and sorted_accounts[-1] != account:
            # print("procesar total")
            if end_grouped_total_lines:
                if len(grouped_total_lines) > 1:
                    new_line = grouped_total_lines[0]
                    grouped_sum_amount_currency = 0.0
                    grouped_sum_debit = 0.0
                    grouped_sum_credit = 0.0
                    grouped_sum_balance = 0.0
                    for line in grouped_total_lines:
                        grouped_sum_debit += line['raw_values'][0]
                        grouped_sum_credit += line['raw_values'][1]
                        grouped_sum_balance += line['raw_values'][2]
                    new_line['columns'] = [{'name': v} for v in ['', '', '', self.format_value(grouped_sum_debit),
                                                                 self.format_value(grouped_sum_credit),
                                                                 self.format_value(grouped_sum_balance)]]
                    lines.append(new_line)
                else:
                    # print('agregando el TOTAL')
                    lines.extend(grouped_total_lines)
                grouped_total_lines = []
                end_grouped_total_lines = False
            grouped_total_lines.append({
                'id': 'general_ledger_total_%s' % company_id.id,
                'name': _('Total'),
                'class': 'total',
                'level': 1,
                'columns': [{'name': v} for v in
                            ['', '', '', '', self.format_value(sum_debit), self.format_value(sum_credit),
                             self.format_value(sum_balance)]],
                'raw_values': [sum_debit, sum_credit, sum_balance]
            })
            # print(len(grouped_total_lines), 'lineas totales')
        else:
            if (len(sorted_accounts) == 1):
                lines.extend(grouped_lines)
                lines.extend(grouped_initial_lines)
                # print(len(grouped_folded_lines))
                if context.get('print_mode'):
                    lines.extend(grouped_folded_lines)
                else:
                    lines.extend(grouped_folded_lines[:2000])

                # print('agregando el folded total line_id una sola cuenta')
                lines.extend(grouped_folded_total_lines)
                lines.extend(grouped_total_lines)
            elif (len(sorted_accounts) > 1):
                new_line = grouped_lines[0]
                grouped_sum_amount_currency = 0.0
                grouped_sum_debit = 0.0
                grouped_sum_credit = 0.0
                grouped_sum_balance = 0.0
                for line in grouped_lines:
                    grouped_sum_amount_currency += line['raw_values'][0]
                    grouped_sum_debit += line['raw_values'][1]
                    grouped_sum_credit += line['raw_values'][2]
                    grouped_sum_balance += line['raw_values'][3]
                new_line['columns'] = [{'name': v} for v in
                                       ['' if grouped_sum_amount_currency == 0.0 else grouped_sum_amount_currency,
                                        self.format_value(grouped_sum_debit), self.format_value(grouped_sum_credit),
                                        self.format_value(grouped_sum_balance)]]
                lines.append(new_line)
                # print('agregando encabezado')

                if grouped_initial_lines:
                    new_line = grouped_initial_lines[0]
                    grouped_sum_amount_currency = 0.0
                    grouped_sum_debit = 0.0
                    grouped_sum_credit = 0.0
                    grouped_sum_balance = 0.0
                    for line in grouped_initial_lines:
                        grouped_sum_amount_currency += line['raw_values'][0]
                        grouped_sum_debit += line['raw_values'][1]
                        grouped_sum_credit += line['raw_values'][2]
                        grouped_sum_balance += line['raw_values'][3]
                    new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                 '' if grouped_sum_amount_currency == 0.0 else grouped_sum_amount_currency,
                                                                 self.format_value(grouped_sum_debit),
                                                                 self.format_value(grouped_sum_credit),
                                                                 self.format_value(grouped_sum_balance)]]
                    # print('agregando el initial')
                    lines.append(new_line)

                    if context.get('print_mode'):
                        lines.extend(grouped_folded_lines)
                    else:
                        lines.extend(grouped_folded_lines[:2000])

                    new_line = grouped_folded_total_lines[0]
                    grouped_sum_amount_currency = 0.0
                    grouped_sum_debit = 0.0
                    grouped_sum_credit = 0.0
                    grouped_sum_balance = 0.0
                    for line in grouped_folded_total_lines:
                        grouped_sum_amount_currency += line['raw_values'][0]
                        grouped_sum_debit += line['raw_values'][1]
                        grouped_sum_credit += line['raw_values'][2]
                        grouped_sum_balance += line['raw_values'][3]
                    formatted_grouped_sum_amount_currency = '' if not account.currency_id else self.with_context(
                        no_format=False).format_value(grouped_sum_amount_currency, currency=account.currency_id)
                    new_line['columns'] = [{'name': v} for v in ['', '', '',
                                                                 '' if grouped_sum_amount_currency == 0.0 else formatted_grouped_sum_amount_currency,
                                                                 self.format_value(grouped_sum_debit),
                                                                 self.format_value(grouped_sum_credit),
                                                                 self.format_value(grouped_sum_balance)]]
                    # print('agregando el folded total en line_id')
                    lines.append(new_line)

                if grouped_total_lines:
                    new_line = grouped_total_lines[0]
                    grouped_sum_amount_currency = 0.0
                    grouped_sum_debit = 0.0
                    grouped_sum_credit = 0.0
                    grouped_sum_balance = 0.0
                    for line in grouped_total_lines:
                        grouped_sum_debit += line['raw_values'][0]
                        grouped_sum_credit += line['raw_values'][1]
                        grouped_sum_balance += line['raw_values'][2]
                    new_line['columns'] = [{'name': v} for v in ['', '', '', self.format_value(grouped_sum_debit),
                                                                 self.format_value(grouped_sum_credit),
                                                                 self.format_value(grouped_sum_balance)]]
                    lines.append(new_line)

        journals = [j for j in options.get('journals') if j.get('selected')]
        if len(journals) == 1 and journals[0].get('type') in ['sale', 'purchase'] and not line_id:
            lines.append({
                'id': 0,
                'name': _('Tax Declaration'),
                'columns': [{'name': v} for v in ['', '', '', '', '', '', '']],
                'level': 1,
                'unfoldable': False,
                'unfolded': False,
            })
            lines.append({
                'id': 0,
                'name': _('Name'),
                'columns': [{'name': v} for v in ['', '', '', '', _('Base Amount'), _('Tax Amount'), '']],
                'level': 2,
                'unfoldable': False,
                'unfolded': False,
            })
            journal_currency = self.env['account.journal'].browse(journals[0]['id']).company_id.currency_id
            for tax, values in self._get_taxes(journals[0]).items():
                base_amount = journal_currency._convert(values['base_amount'], used_currency, company_id,
                                                        options['date']['date_to'])
                tax_amount = journal_currency._convert(values['tax_amount'], used_currency, company_id,
                                                       options['date']['date_to'])
                lines.append({
                    'id': '%s_tax' % (tax.id,),
                    'name': tax.name + ' (' + str(tax.amount) + ')',
                    'caret_options': 'account.tax',
                    'unfoldable': False,
                    'columns': [{'name': v} for v in
                                [self.format_value(base_amount), self.format_value(tax_amount), '']],
                    'colspan': 5,
                    'level': 4,
                })

        try:
            lines.append(total_pl_line)
        except (UnboundLocalError, NameError):
            pass

        if self.env.context.get('aml_only', False):
            return aml_lines
        return lines
