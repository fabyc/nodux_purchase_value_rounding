# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from .purchase import *

def register():
    Pool.register(
        Purchase,
        module='nodux_purchase_value_rounding', type_='model')
