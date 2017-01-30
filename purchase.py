#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import datetime
from decimal import Decimal
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond import backend
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Bool, If, PYSONEncoder, Id
from trytond.transaction import Transaction

__all__ = ['Purchase', 'PurchaseLine']
__metaclass__ = PoolMeta
_ZERO = Decimal(0)

class Purchase():
    'Purchase'
    __name__ = 'purchase.purchase'

    @classmethod
    def __setup__(cls):
        super(Purchase, cls).__setup__()

    @fields.depends('lines', 'currency', 'party')
    def on_change_lines(self):
        pool = Pool()
        Tax = pool.get('account.tax')
        Invoice = pool.get('account.invoice')
        Configuration = pool.get('account.configuration')

        config = Configuration(1)

        changes = {
            'untaxed_amount': Decimal('0.0'),
            'tax_amount': Decimal('0.0'),
            'total_amount': Decimal('0.0'),
            }
        if self.lines:
            context = self.get_tax_context()
            taxes = {}

            def round_taxes():
                if self.currency:
                    for key, value in taxes.iteritems():
                        values = str(value).split(".")
                        if len(values) >1:
                            if str(values[1][2]) == str("5") and str(values[1][3] == str("0")):
                                value = value + Decimal(0.0001)
                        taxes[key] = self.currency.round(value)

            for line in self.lines:
                if getattr(line, 'type', 'line') != 'line':
                    continue
                changes['untaxed_amount'] += (getattr(line, 'amount', None)
                    or Decimal(0))

                with Transaction().set_context(context):
                    tax_list = Tax.compute(getattr(line, 'taxes', []),
                        getattr(line, 'unit_price', None) or Decimal('0.0'),
                        getattr(line, 'quantity', None) or 0.0)
                for tax in tax_list:
                    key, val = Invoice._compute_tax(tax, 'in_invoice')
                    if key not in taxes:
                        taxes[key] = val['amount']
                    else:
                        taxes[key] += val['amount']
                if config.tax_rounding == 'line':
                    round_taxes()
            if config.tax_rounding == 'document':
                round_taxes()
            changes['tax_amount'] = sum(taxes.itervalues(), Decimal('0.0'))
        if self.currency:
            changes['untaxed_amount'] = self.currency.round(
                changes['untaxed_amount'])
            changes['tax_amount'] = self.currency.round(changes['tax_amount'])
        changes['total_amount'] = (changes['untaxed_amount']
            + changes['tax_amount'])
        if self.currency:
            changes['total_amount'] = self.currency.round(
                changes['total_amount'])
        return changes

    def get_tax_amount(self):
        pool = Pool()
        Tax = pool.get('account.tax')
        Invoice = pool.get('account.invoice')
        Configuration = pool.get('account.configuration')

        config = Configuration(1)

        context = self.get_tax_context()
        taxes = {}

        def round_taxes():

            for key, value in taxes.iteritems():
                values = str(value).split(".")
                if len(values) >1:
                    if str(values[1][2]) == str("5") and str(values[1][3] == str("0")):
                        value = value + Decimal(0.0001)
                taxes[key] = self.currency.round(value)

        for line in self.lines:
            if line.type != 'line':
                continue
            with Transaction().set_context(context):
                tax_list = Tax.compute(line.taxes, line.unit_price,
                    line.quantity)
            for tax in tax_list:
                key, val = Invoice._compute_tax(tax, 'in_invoice')
                if key not in taxes:
                    taxes[key] = val['amount']
                else:
                    taxes[key] += val['amount']
            if config.tax_rounding == 'line':
                round_taxes()
        if config.tax_rounding == 'document':
            round_taxes()
        return sum(taxes.itervalues(), _ZERO)

class PurchaseLine:
    __name__ = 'purchase.line'

    @classmethod
    def __setup__(cls):
        super(PurchaseLine, cls).__setup__()
        cls.gross_unit_price.digits = (16, 6)
