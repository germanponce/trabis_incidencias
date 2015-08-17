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


from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import pooler, tools
from openerp import netsvc
from openerp import release
import datetime
from pytz import timezone
import pytz
from dateutil.relativedelta import relativedelta
from datetime import timedelta

import time
import os

class account_move(osv.osv):
    _name = 'account.move'
    _inherit ='account.move'
    _columns = {
        }

    _defaults = {
        }

    def button_cancel(self, cr, uid, ids, context=None):
        res = super(account_move, self).button_cancel(cr, uid, ids, context)
        for rec in self.browse(cr, uid, ids, context=None):
            if rec.period_id.state == 'done':
                period = rec.period_id.name
                raise osv.except_osv(_('Error!'), 
                _('No puedes Cancelar un asiento si el Periodo [%s] esta Cerrado. Por favor reabre el Periodo.\
                    \n Si piensa que esto es un Error contacta al Administrador.' % period ))
            elif rec.period_id.state == 'draft' and rec.journal_id.update_posted == False:
                raise osv.except_osv(_('Error!'), 
                _('No puedes cancelar el Asiento ya que el Diario [%s] no lo Permite. Activa el campo Permitir Cancelacion.\
                    \n Si piensa que esto es un Error contacta al Administrador. [%s]' % period ))
            else:
                return res
        return res


    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        
        # valid_moves = self.validate(cr, uid, ids, context)

        # if not valid_moves:
        #     raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        if invoice:
            if invoice.company_id.currency_id.id != invoice.currency_id.id:
                if invoice.type in ('in_invoice','in_refund'):
                    move_line = self.pool.get('account.move.line')
                    cr.execute("select sum(debit) from account_move_line where move_id=%s" %ids[0])
                    debit_sum = cr.fetchall()[0][0]
                    cr.execute("select sum(credit) from account_move_line where move_id=%s" %ids[0])
                    credit_sum = cr.fetchall()[0][0]
                    invoice_amount_total = invoice.amount_total
                    cr.execute("select id from account_move_line where abs(amount_currency) = %s and move_id = %s",
                        (invoice_amount_total, ids[0]))
                    move_id = cr.fetchall()[0][0]
                    # move_id = self.pool.get('account.move.line').search(cr, uid,
                    #     [('amount_currency','=',invoice_amount_total)])
                    diff = 0.0
                    move_br = move_line.browse(cr, uid, move_id, context=None)
                    vals_finales = {}
                    if debit_sum > credit_sum:
                        diff = debit_sum - credit_sum
                        if diff != 0.0:
                            if move_br.debit > 0.0:
                                total_new = move_br.debit + diff
                                # move_br.write({'debit':total_new})
                                vals_finales.update({'debit':total_new})
                            else:
                                total_new = move_br.credit + diff
                                # move_br.write({'credit':total_new})
                                vals_finales.update({'credit':total_new})

                    else:
                        diff = credit_sum - debit_sum
                        if diff != 0.0:
                            if move_br.debit > 0.0:
                                total_new = move_br.debit - diff
                                # move_br.write({'debit':total_new})
                                vals_finales.update({'debit':total_new})
                            else:
                                total_new = move_br.credit - diff
                                # move_br.write({'credit':total_new})
                                vals_finales.update({'credit':total_new})
                    if diff < 1.0:
                        valid_moves = ids
                        move_br.write(vals_finales)
                    else:
                        valid_moves = self.validate(cr, uid, ids, context)
                        if not valid_moves:
                            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
            

                else:
                    valid_moves = self.validate(cr, uid, ids, context)

                    if not valid_moves:
                        raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
            else:
                valid_moves = self.validate(cr, uid, ids, context)

                if not valid_moves:
                    raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        else:
            valid_moves = self.validate(cr, uid, ids, context)

            if not valid_moves:
                raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name =='/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.internal_number:
                    new_name = invoice.internal_number
                else:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                        new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))

                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name})

        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
        return True

    def _check_period(self, cr, uid, ids, context=None): 
        for rec in self.browse(cr, uid, ids, context=None):
            if rec.period_id.state == 'done':
                return False
        return True
    _constraints = [(_check_period, 'Error: No puedes crear una Poliza para un Periodo Cerrado.', ['period_id']), ] 