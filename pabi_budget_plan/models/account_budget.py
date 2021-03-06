# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountBudget(models.Model):
    _inherit = 'account.budget'
    _order = 'create_date desc'

    policy_amount = fields.Float(
        string='Policy Amount',
        readonly=True,
    )

    @api.multi
    def _get_doc_number(self):
        self.ensure_one()
        _prefix = 'CTRL'
        _prefix2 = {'unit_base': 'UNIT',
                    'invest_asset': 'ASSET',
                    'project_base': 'PROJ',
                    'invest_construction': 'CONST',
                    'personnel': 'PERSONNEL'}
        _prefix3 = {'unit_base': 'section_id',
                    'invest_asset': 'org_id',
                    'project_base': 'program_id',
                    'invest_construction': 'org_id',
                    'personnel': False}
        prefix2 = _prefix2[self.chart_view]
        prefix3 = 'NSTDA'
        if _prefix3[self.chart_view]:
            obj = self[_prefix3[self.chart_view]]
            prefix3 = obj.code or obj.name_short or obj.name
        name = '%s/%s/%s/%s' % (_prefix, prefix2,
                                self.fiscalyear_id.code, prefix3)
        return name

    @api.model
    def create(self, vals):
        budget = super(AccountBudget, self).create(vals)
        budget_level = budget.budget_level_id
        if budget_level.budget_release == 'manual_header' and \
                budget_level.release_follow_policy and \
                'policy_amount' in vals:
            vals['to_release_amount'] = vals['policy_amount']
            budget.write(vals)
        # Numbering
        budget.name = budget._get_doc_number()
        # --
        return budget

    @api.multi
    def write(self, vals):
        if 'policy_amount' in vals:
            for budget in self:
                budget_level = budget.budget_level_id
                if budget_level.budget_release == 'manual_header' and \
                        budget_level.release_follow_policy:
                    vals['to_release_amount'] = vals['policy_amount']
                super(AccountBudget, budget).write(vals)
        else:
            super(AccountBudget, self).write(vals)
        for rec in self:
            # Name
            if rec.name != rec._get_doc_number():
                rec._write({'name': rec._get_doc_number()})
            # If there is policy amount, some fields can't be changed.
            if rec.policy_amount:
                no_edit_fields = ['section_id', 'fiscalyear_id']
                if set(no_edit_fields) & set(vals.keys()):
                    raise ValidationError(
                        _('With policy amount, fields edit not allow for: %s')
                        % ', '.join(no_edit_fields))
        return True

    @api.multi
    @api.constrains('chart_view', 'fiscalyear_id', 'section_id', 'program_id',
                    'org_id', 'personnel_costcenter_id')
    def _check_fiscalyear_section_unique(self):
        for budget in self:
            budget = self.search(
                [('chart_view', '=', budget.chart_view),
                 ('fiscalyear_id', '=', budget.fiscalyear_id.id),
                 ('section_id', '=', budget.section_id.id),
                 ('program_id', '=', budget.program_id.id),
                 ('org_id', '=', budget.org_id.id),
                 ('personnel_costcenter_id', '=',
                  budget.personnel_costcenter_id.id),
                 ])
            if len(budget) > 1:
                raise ValidationError(
                    _('Duplicated budget on the same fiscal year!'))

    @api.multi
    def unlink(self):
        for policy in self:
            if policy.state not in ('draft', 'cancel'):
                raise ValidationError(
                    _('Cannot delete budget(s)\
                    which are not in draft or cancelled.'))
        return super(AccountBudget, self).unlink()

    @api.model
    def generate_project_base_controls(self, fiscalyear_id=None):
        if not fiscalyear_id:
            raise ValidationError(_('No fiscal year provided!'))
        fiscal = self.env['account.fiscalyear'].browse(fiscalyear_id)
        # Find existing controls, and exclude them
        controls = self.search([('fiscalyear_id', '=', fiscalyear_id),
                                ('chart_view', '=', 'project_base')])
        _ids = controls.mapped('program_id')._ids
        # Find Programs
        programs = self.env['res.program'].search([('id', 'not in', _ids),
                                                   ('special', '=', False)])
        control_ids = []
        for program in programs:
            control = self.create({'chart_view': 'project_base',
                                   'fiscalyear_id': fiscalyear_id,
                                   'date_from': fiscal.date_start,
                                   'date_to': fiscal.date_stop,
                                   'program_id': program.id, })
            control_ids.append(control.id)
        return control_ids

    @api.model
    def generate_invest_construction_controls(self, fiscalyear_id=None):
        if not fiscalyear_id:
            raise ValidationError(_('No fiscal year provided!'))
        fiscal = self.env['account.fiscalyear'].browse(fiscalyear_id)
        # Find existing controls, and exclude them
        controls = self.search([('fiscalyear_id', '=', fiscalyear_id),
                                ('chart_view', '=', 'invest_construction')])
        _ids = controls.mapped('org_id')._ids
        # Find orgs
        orgs = self.env['res.org'].search([('id', 'not in', _ids),
                                           ('special', '=', False)])
        control_ids = []
        for org in orgs:
            control = self.create({'chart_view': 'invest_construction',
                                   'fiscalyear_id': fiscalyear_id,
                                   'date_from': fiscal.date_start,
                                   'date_to': fiscal.date_stop,
                                   'org_id': org.id,
                                   'user_id': False})
            control_ids.append(control.id)
        return control_ids
