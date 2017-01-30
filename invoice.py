from decimal import Decimal
from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Eval
from trytond.config import config

__all__ = ['InvoiceLine']
__metaclass__ = PoolMeta


class InvoiceLine:
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        cls.gross_unit_price.digits = (16, 6)
