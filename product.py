#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Get, If, Bool
from trytond.pool import PoolMeta

__all__ = ['Product', 'ProductBom']
__metaclass__ = PoolMeta


class Product:
    __name__ = 'product.product'

    boms = fields.One2Many('product.product-production.bom', 'product',
        'BOMs', order=[('sequence', 'ASC'), ('id', 'ASC')],
        states={
            'invisible': Eval('type', 'service') == 'service',
            },
        depends=['type'])

    @classmethod
    def __setup__(cls):
        super(Product, cls).__setup__()
        cls._constraints += [
            ('check_bom_recursion', 'recursive_bom'),
            ]
        cls._error_messages.update({
                'recursive_bom': 'You can not create recursive BOMs!',
                })

    def check_bom_recursion(self, product=None):
        '''
        Check BOM recursion
        '''
        if product is None:
            product = self
        for product_bom in self.boms:
            for input_ in product_bom.bom.inputs:
                if input_.product == product:
                    return False
                if not input_.product.check_bom_recursion(product=product):
                    return False
        return True

    @classmethod
    def copy(cls, products, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('boms', None)
        return super(Product, cls).copy(products, default=default)


class ProductBom(ModelSQL, ModelView):
    'Product - BOM'
    __name__ = 'product.product-production.bom'

    product = fields.Many2One('product.product', 'Product',
        ondelete='CASCADE', select=1, required=True,
        domain=[
            ('type', '!=', 'service'),
            ])
    bom = fields.Many2One('production.bom', 'BOM', ondelete='CASCADE',
        select=1, required=True, domain=[
            ('output_products', '=', If(Bool(Eval('product')),
                    Eval('product', 0),
                    Get(Eval('_parent_product', {}), 'id', 0))),
            ], depends=['product'])
    sequence = fields.Integer('Sequence')

    @classmethod
    def __setup__(cls):
        super(ProductBom, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    def get_rec_name(self, name):
        return self.bom.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('bom.rec_name',) + tuple(clause[1:])]
