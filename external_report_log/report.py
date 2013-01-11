# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2013 credativ ltd (<http://www.credativ.co.uk>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import pooler
from osv import osv, fields

import datetime

class external_log(osv.osv):
    _name = 'external.log'
    _description = 'External referential transfer log'
    _order = 'start_time'

    _columns = {
        'name': fields.char('Execution reference', type='char', size=15, required=True),
        'referential_id': fields.many2one('external.referential', 'External referential', required=True, readonly=True),
        'retry_of': fields.many2one('external.log', 'Retry of', readonly=True),
        'start_time': fields.datetime('Start time', required=True, readonly=True),
        'end_time': fields.datetime('End time', required=True, readonly=True),
        'status': fields.selection([('in-progress', 'In progress'),
                                    ('exported-fail', 'Exported - with errors'),
                                    ('exported-success', 'Exported - correct'),
                                    ('complete-rejections', 'Complete - rejections'),
                                    ('complete-complete', 'Complete')], required=True, readonly=True),
        'line_ids': fields.one2many('external.report.line', 'external_log_id', 'Report lines')
        }

    _defaults = {
        'name': lambda self, cr, uid, context: self.pool.get('ir.sequence').next_by_code(cr, uid, 'external_report_log.extref_exec_id', context=context)
        }

    def start_transfer(self, cr, uid, ids, referential_id, context=None):
        if context is None:
            context = {}

        return self.create(cr, uid, {'referential_id': referential_id,
                                     'retry_of': context.get('retry_of_execution', None),
                                     'start_time': datetime.datetime.now(),
                                     'status': 'in-progress'}, context=context)

    def end_transfer(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        if isinstance(ids, (list, tuple)):
            ids = ids[0]

        log = self.browse(cr, uid, ids)
        if not log:
            raise ValueError('Cannot call end_transfer on non-existant log: %d' % (ids,))

        self.write(cr, uid, ids, {'end_time': datetime.datetime.now(),
                                  'status': all([line.state == 'exported' for line in log.line_ids]) and 'exported-success' or 'exported-fail'})


external_log()

        
class external_report_lines(osv.osv):
    _inherit = 'external.report.line'

    _columns = {
        'state': fields.selection([('exported','Exported'),
                                   ('failed','Failed'),
                                   ('confirmed','Confirmed'),
                                   ('rejected','Rejected')], required=True, readonly=True),
        'external_log_id': fields.many2one('external.log', 'External log', required=True, readonly=True),
        'message': fields.text('Error message', readonly=True)
        }

    def log_system_fail(self, cr, uid, model, action, referential_id, exc, msg=None, defaults=None, context=None):
        defaults = defaults or {}
        context = context or {}
        exc = exc or Exception(msg)

        log_cr = pooler.get_db(cr.dbname).cursor()

        try:
            origin_defaults = defaults.copy()
            origin_context = context.copy()
            # connection object cannot be kept in text
            if origin_context.get('conn_obj', False):
                del origin_context['conn_obj']
            info = self._prepare_log_info(
                log_cr, uid, origin_defaults, origin_context, context=context)
            vals = self._prepare_log_vals(
                log_cr, uid, model, action, res_id=None, external_id=None,
                referential_id=referential_id, data_record=None, context=context)
            vals.update(info)
            vals['message'] = msg
            report = self.create(log_cr, uid, vals, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return report

    def log_system_success(self, cr, uid, model, action, referential_id, context=None):
        raise NotImplementedError()

    def retry_system(self, cr, uid):
        raise NotImplementedError()

    def _log(self, cr, uid, model, action, referential_id, status, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        defaults = defaults or {}
        context = context or {}

        log_cr = pooler.get_db(cr.dbname).cursor()

        try:
            exists = self.search(cr, uid, [('model','=',model),
                                           ('action','=',action),
                                           ('referential_id','=',referential_id),
                                           ('res_id','=',res_id)], context=context)
            origin_defaults = defaults.copy()
            origin_context = context.copy()
            # connection object cannot be serialised
            if origin_context.get('conn_obj', False):
                del origin_context['conn_obj']
            info = self._prepare_log_info(log_cr, uid, origin_defaults, origin_context, context=context)
            if exists:
                self.write(log_cr, uid, exists[0], info, context=context)
            else:
                vals = self._prepare_log_vals(log_cr, uid, model, action, res_id=None, external_id=None, referential_id=referential_id, data_record=None, context=context)
                vals.update(info)
                vals['status'] = status
                report = self.create(log_cr, uid, vals, context=context)
        except:
            log_cr.rollback()
            raise
        else:
            log_cr.commit()
        finally:
            log_cr.close()
        return report
        
    def log_exported(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, data_record=None, defaults=None, context=None):
        return self._log(cr, uid, model, action, referential_id, 'exported', res_id, external_id, data_record, defaults, context=context)

    def log_failed(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, data_record=None, defaults=None, context=None):

        res = super(external_report_lines, self).log_failed(cr, uid, model, action, referential_id, res_id, external_id, data_record, defaults, context)
        return res

    def log_success(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, context=None):

        # FIXME The super method actually removes the fail log, so we
        # probably don't actually want to do this
        res = super(external_report_lines, self).log_success(cr, uid, model, action, referential_id, res_id, external_id, context)
        return res

    def log_rejected(self, cr, uid, model, action, referential_id, res_id=None, external_id=None, context=None):
        return self._log(cr, uid, model, action, referential_id, 'rejected', res_id, external_id, context=context)

    def retry(self, cr, uid, ids, context=None):

        res = super(external_report_lines, self).retry(cr, uid, ids, context)
        return res

external_report_lines()
