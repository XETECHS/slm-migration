# -*- coding: utf-8 -*-


from odoo import models, api, _, fields


class report_account_coa(models.AbstractModel):
    _inherit = "account.coa.report"

    # def _get_templates(self):
    #     templates = super(report_account_coa, self)._get_templates()
    #     templates['main_table_header_template'] = 'slm_trial_balance_consolidated.template_coa_table_header'
    #     return templates

    # def _get_super_columns(self, options):
    #     date_cols = options.get('date') and [options['date']] or []
    #     date_cols += (options.get('comparison') or {}).get('periods', [])

    #     columns = [{'string': _('Initial Balance')}]
    #     columns += reversed(date_cols)
    #     columns += [{'string': 'Total'}]
    #     columns += [{'string': _('Balance')}]
    #     columns += [{'string': _('Profit & Loss')}]

    #     return {'columns': columns, 'x_offset': 1, 'merge': 2}

    # def _get_columns_name(self, options):
    #     columns = [
    #         {'name': '', 'style': 'width:40%'},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #     ]
    #     if options.get('comparison') and options['comparison'].get('periods'):
    #         columns += [
    #             {'name': _('Debit'), 'class': 'number'},
    #             {'name': _('Credit'), 'class': 'number'},
    #         ] * len(options['comparison']['periods'])
    #     return columns + [
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #         {'name': _('Debit'), 'class': 'number'},
    #         {'name': _('Credit'), 'class': 'number'},
    #     ]

    def _post_process(self, grouped_accounts, initial_balances, options, comparison_table):
        lines = []
        context = self.env.context
        company_id = context.get('company_id') or self.env.user.company_id
        title_index = ''
        sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
        zero_value = ''
        sum_columns = [0, 0, 0, 0, 0, 0, 0, 0]
        for period in range(len(comparison_table)):
            sum_columns += [0, 0]
        for account in sorted_accounts:
            # skip accounts with all periods = 0 and no initial balance
            non_zero = False
            for p in range(len(comparison_table)):
                if (grouped_accounts[account][p]['debit'] or grouped_accounts[account][p]['credit']) or\
                        not company_id.currency_id.is_zero(initial_balances.get(account, 0)):
                    non_zero = True
            if not non_zero:
                continue

            initial_balance = initial_balances.get(account, 0.0)
            sum_columns[0] += initial_balance if initial_balance > 0 else 0
            sum_columns[1] += -initial_balance if initial_balance < 0 else 0
            cols = [
                {'name': initial_balance > 0 and self.format_value(
                    initial_balance) or zero_value, 'no_format_name': initial_balance > 0 and initial_balance or 0},
                {'name': initial_balance < 0 and self.format_value(
                    -initial_balance) or zero_value, 'no_format_name': initial_balance < 0 and abs(initial_balance) or 0},
            ]
            total_periods = 0
            for period in range(len(comparison_table)):
                amount = grouped_accounts[account][period]['balance']
                debit = grouped_accounts[account][period]['debit']
                credit = grouped_accounts[account][period]['credit']
                total_periods += amount
                cols += [{'name': debit > 0 and self.format_value(debit) or zero_value, 'no_format_name': debit > 0 and debit or 0},
                         {'name': credit > 0 and self.format_value(credit) or zero_value, 'no_format_name': credit > 0 and abs(credit) or 0}]
                # In sum_columns, the first 2 elements are the initial balance's Debit and Credit
                # index of the credit of previous column generally is:
                p_indice = period * 2 + 1
                sum_columns[(p_indice) + 1] += debit if debit > 0 else 0
                sum_columns[(p_indice) + 2] += credit if credit > 0 else 0

            total_amount = initial_balance + total_periods
            sum_columns[-6] += total_amount if total_amount > 0 else 0
            sum_columns[-5] += -total_amount if total_amount < 0 else 0
            cols += [
                {'name': total_amount > 0 and self.format_value(
                    total_amount) or zero_value, 'no_format_name': total_amount > 0 and total_amount or 0},
                {'name': total_amount < 0 and self.format_value(
                    -total_amount) or zero_value, 'no_format_name': total_amount < 0 and abs(total_amount) or 0},
            ]
            if int(account.code[0]) >= 4 and account.code != '999999':
                cols += [{'name': zero_value, 'no_format_name': zero_value},
                         {'name': zero_value, 'no_format_name': zero_value}]
                sum_columns[-2] += total_amount if total_amount > 0 else 0
                sum_columns[-1] += -total_amount if total_amount < 0 else 0
            else:
                sum_columns[-4] += total_amount if total_amount > 0 else 0
                sum_columns[-3] += -total_amount if total_amount < 0 else 0
            cols += [
                {'name': total_amount > 0 and self.format_value(
                    total_amount) or zero_value, 'no_format_name': total_amount > 0 and total_amount or 0},
                {'name': total_amount < 0 and self.format_value(
                    -total_amount) or zero_value, 'no_format_name': total_amount < 0 and abs(total_amount) or 0},
            ]
            name = account.code + " " + account.name
            lines.append({
                'id': account.id,
                'name': len(name) > 40 and not context.get('print_mode') and name[:40]+'...' or name,
                'title_hover': name,
                'columns': cols,
                'unfoldable': False,
                'caret_options': 'account.account',
            })

        lines.append({
            'id': 'grouped_accounts_total',
            'name': _('Total'),
            'class': 'total',
            'columns': [{'name': self.format_value(v)} for v in sum_columns],
            'level': 1,
        })

        difference_columns = [{'name': zero_value}] * len(sum_columns)
        difference_columns[-2] = {'name': self.format_value(
            sum_columns[-2] - sum_columns[-1])}
        difference_columns[-4] = {'name': self.format_value(
            sum_columns[-4] - sum_columns[-3])}

        lines.append({
            'id': 'difference_total',
            'name': '',
            'class': 'difference',
            'columns': difference_columns,
        })
        return lines

    # @api.model
    # def _get_lines(self, options, line_id=None):
    #     context = self.env.context
    #     company_id = context.get('company_id') or self.env.user.company_id
    #     grouped_accounts = {}
    #     initial_balances = {}
    #     comparison_table = [options.get('date')]
    #     comparison_table += options.get(
    #         'comparison') and options['comparison'].get('periods') or []

    #     # get the balance of accounts for each period
    #     period_number = 0
    #     for period in reversed(comparison_table):
    #         account_codes = {}
    #         res = self.with_context(date_from_aml=period['date_from'], date_to=period['date_to'], date_from=period['date_from'] and company_id.compute_fiscalyear_dates(fields.Date.from_string(period['date_from']))['date_from'] or None)._group_by_account_id(
    #             options, line_id)  # Aml go back to the beginning of the user chosen range but the amount on the account line should go back to either the beginning of the fy or the beginning of times depending on the account
    #         if period_number == 0:
    #             initial_balances = dict(
    #                 [(k, res[k]['initial_bal']['balance']) for k in res])
    #             initial_balances = {}
    #             initial_balances_codes = {}
    #             for k in res:
    #                 if k.code not in initial_balances_codes:
    #                     initial_balances[k] = res[k]['initial_bal']['balance']
    #                     initial_balances_codes[k.code] = k
    #                 else:
    #                     parent_account = initial_balances_codes[k.code]
    #                     initial_balances[parent_account] += res[k]['initial_bal']['balance']
    #         for account in res:
    #             if account not in grouped_accounts and account.code not in account_codes:
    #                 grouped_accounts[account] = [
    #                     {'balance': 0, 'debit': 0, 'credit': 0} for p in comparison_table]
    #             if account.code not in account_codes:
    #                 account_codes[account.code] = account
    #                 grouped_accounts[account][period_number]['balance'] = res[account]['balance'] - \
    #                     res[account]['initial_bal']['balance']
    #                 grouped_accounts[account][period_number]['debit'] = res[account]['debit'] - \
    #                     res[account]['initial_bal']['debit']
    #                 grouped_accounts[account][period_number]['credit'] = res[account]['credit'] - \
    #                     res[account]['initial_bal']['credit']
    #             else:
    #                 parent_account = account_codes[account.code]
    #                 grouped_accounts[parent_account][period_number]['balance'] += res[account]['balance'] - \
    #                     res[account]['initial_bal']['balance']
    #                 grouped_accounts[parent_account][period_number]['debit'] += res[account]['debit'] - \
    #                     res[account]['initial_bal']['debit']
    #                 grouped_accounts[parent_account][period_number]['credit'] += res[account]['credit'] - \
    #                     res[account]['initial_bal']['credit']

    #         period_number += 1
    #     # build the report
    #     lines = self._post_process(
    #         grouped_accounts, initial_balances, options, comparison_table)
    #     return lines
