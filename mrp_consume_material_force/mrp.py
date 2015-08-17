# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv, orm
from datetime import time, datetime
from tools.translate import _
from openerp import tools
import netsvc
from openerp.tools import float_compare
from openerp import SUPERUSER_ID

class mrp_production(osv.osv):
    _name = 'mrp.production'
    _inherit ='mrp.production'
    _columns = {
        }

    _defaults = {
        }


    def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
        res = super(mrp_production, self).action_produce(cr, uid, production_id, production_qty, production_mode, context)
        ######### FUNCIONES QUE AGREGUE PARA LOS MOVIMIENTOS NUEVOS ############
        for rec in self.browse(cr, uid, [production_id], context=None):
            ######### FINALIZANDO LOS PRODUCTOS QUE FALTAN POR CONSUMIR ############
            if rec.state == 'done':
                for moves in rec.move_lines:
                    moves.action_done()
        ############### INTERRUPCION DEL FLUJO PYTHON ############################
        # raise osv.except_osv(_('Interrupcion del Flujo!'), 
        #                      _('Debugeando el Codigo de Creacion de Factura desde lineas de Compra') )

        return res

mrp_production()