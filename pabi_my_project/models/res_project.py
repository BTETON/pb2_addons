# -*- coding: utf-8 -*-
from openerp import models, api, fields, _
from openerp import tools
from openerp.exceptions import ValidationError
from openerp.addons.document_status_history.models.document_history import \
    LogCommon


MY_PROJECT_STATES = [('draft', 'Draft'),
                     ('submit', 'Submitted'),
                     ('unapprove', 'Un-Approved'),
                     ('approve', 'Approved'),
                     ('reject', 'Rejected'),
                     ('delete', 'Deleted'),
                     ('cancel', 'Cancelled'),
                     ('close', 'Closed'),
                     ]


class ResProject(LogCommon, models.Model):
    _inherit = 'res.project'

    state = fields.Selection(
        MY_PROJECT_STATES,
        string='Status',
        required=True,
        copy=False,
        default='draft',
    )
    state2 = fields.Selection(
        MY_PROJECT_STATES,
        string='Status',
        related='state',
        help="For display purposes",
    )
    date_start = fields.Date(
        string='Start Date',
    )
    date_approve = fields.Date(
        string='Approved Date',
    )
    date_end = fields.Date(
        string='End Date',
    )
    project_duration = fields.Integer(
        string='Duration',
    )
    project_status = fields.Char(
        string='Project Status',
    )
    project_date_end_proposal = fields.Date(
        string='Project End Date (by proposal)',
    )
    project_date_end_extension = fields.Date(
        string='Project End Date (by extension)',
    )
    project_date_close = fields.Date(
        string='Project Close Date',
    )
    pm_employee_id = fields.Many2one(
        'hr.employee',
        string='Project Manager',
        required=True,
    )
    pm_section_id = fields.Many2one(
        'res.section',
        string='Project Manager Section',
        related='pm_employee_id.section_id',
    )
    owner_division_id = fields.Many2one(
        'res.division',
        string='Project Division',
        related='pm_employee_id.section_id.division_id',
    )
    analyst_employee_id = fields.Many2one(
        'hr.employee',
        string='Project Analyst',
        required=True,
    )
    analyst_section_id = fields.Many2one(
        'res.section',
        string='Project Analyst Section',
        related='analyst_employee_id.section_id',
    )
    ref_program_id = fields.Many2one(
        'res.program',
        string='Program Reference',
    )
    external_fund_type = fields.Selection(
        [('government', 'Government'),
         ('private', 'Private Organization'),
         ('oversea', 'Oversea')],
        string='External Fund Type',
    )
    external_fund_name = fields.Char(
        string='External Fund Name',
    )
    priority = fields.Char(
        string='Priority',
    )
    budget_plan_ids = fields.One2many(
        'res.project.budget.plan',
        'project_id',
        string='Budget Lines',
    )
    budget_release_ids = fields.One2many(
        'res.project.budget.release',
        'project_id',
        string='Budget Release History',
    )
    fiscalyear_ids = fields.Many2many(
        'account.fiscalyear',
        'res_project_fiscalyear_rel', 'project_id', 'fiscalyear_id',
        string='Related Fiscal Years',
        compute='_compute_fiscalyear_ids',
        store=True,
        help="All related fiscal years for this project"
    )
    budget_count = fields.Integer(
        string='Budget Control Count',
        compute='_compute_budget_count',
    )
    budget_to_sync_count = fields.Integer(
        string='Budget Need Sync Count',
        compute='_compute_budget_to_sync_count',
    )
    summary_ids = fields.One2many(
        'res.project.budget.summary',
        'project_id',
        string='Project Summary',
        readonly=True,
    )
    member_ids = fields.One2many(
        'res.project.member',
        'project_id',
        string='Project Member',
        copy=False,
    )
    nstda_strategy_id = fields.Many2one(
        'project.nstda.strategy',
        string='NSTDA Strategy',
    )
    # Project Performance (myPerformance)
    pfm_publications = fields.Integer(
        string='Publication',
    )
    pfm_patents = fields.Integer(
        string='Patent',
    )
    pfm_petty_patents = fields.Integer(
        string='Petty Patent',
    )
    pfm_copyrights = fields.Integer(
        string='Copy Right',
    )
    pfm_trademarks = fields.Integer(
        string='Trademark',
    )
    pfm_plant_varieties = fields.Integer(
        string='Plant Varieties',
    )
    pfm_laboratory_prototypes = fields.Integer(
        string='Laboratory Prototype',
    )
    pfm_field_prototypes = fields.Integer(
        string='Field Prototype',
    )
    pfm_commercial_prototypes = fields.Integer(
        string='Commercial Prototype',
    )
    # Project Detail    # Project Detail
    fy1 = fields.Float(
        string='FY1',
    )
    fy2 = fields.Float(
        string='FY2',
    )
    fy3 = fields.Float(
        string='FY3',
    )
    fy4 = fields.Float(
        string='FY4',
    )
    fy5 = fields.Float(
        string='FY5',
    )
    revenue_budget = fields.Float(
        string='Revenue Budget',
    )
    overall_revenue_plan = fields.Float(
        string='Overall Revenue Plan',
    )
    overall_expense_budget = fields.Float(
        string='Overall Expense Budget',
    )
    project_kind = fields.Selection(
        [('research', 'Research'),
         ('non_research', 'Non-Research'),
         ('management', 'Management'),
         ('construction', 'Construction'), ],
        string='Project Kind',
    )
    project_objective = fields.Char(
        string='Objective',
    )
    project_type = fields.Char(
        string='Project Type',
    )

    @api.onchange('pm_employee_id')
    def _onchange_user_id(self):
        self.pm_section_id = self.pm_employee_id.section_id
        self.owner_disivion_id = self.pm_employee_id.section_id.division_id

    @api.onchange('analyst_employee_id')
    def _onchange_analyst_employee_id(self):
        self.analyst_section_id = self.analyst_employee_id.section_id

    @api.model
    def find_active_project_budget(self, fiscalyear_ids, program_ids):
        budgets = self.env['account.budget'].search([
            ('chart_view', '=', 'project_base'),
            ('fiscalyear_id', 'in', fiscalyear_ids),
            ('program_id', 'in', program_ids)])
        return budgets

    @api.multi
    def _compute_budget_count(self):
        for rec in self:
            # Show all budget control with same program and fiscalyear
            budgets = self.find_active_project_budget(
                rec.fiscalyear_ids.ids, [rec.program_id.id])
            rec.budget_count = len(budgets)

    @api.multi
    @api.depends('budget_plan_ids')
    def _compute_budget_to_sync_count(self):
        for rec in self:
            to_sync_fiscals = rec.budget_plan_ids.filtered(
                lambda l: not l.synced).mapped('fiscalyear_id')
            budgets = self.find_active_project_budget(
                to_sync_fiscals.ids, [rec.program_id.id])
            rec.budget_to_sync_count = len(budgets)

    @api.multi
    @api.depends('budget_plan_ids.fiscalyear_id')
    def _compute_fiscalyear_ids(self):
        for project in self:
            fiscalyear_ids = [x.fiscalyear_id.id
                              for x in project.budget_plan_ids]
            project.fiscalyear_ids = list(set(fiscalyear_ids))

    @api.multi
    def sync_project_plan_to_budget_line(self, fiscalyear_ids=False):
        """
        fiscalyear_ids specify which year to sync, otherwise, all sync.
        only sync if synced=False
        """
        for project in self:
            # Find phase with vaild sync history
            plan_syncs = not fiscalyear_ids and project.budget_plan_ids or \
                project.budget_plan_ids.filtered(
                    lambda l: l.fiscalyear_id.id in fiscalyear_ids)
            if not plan_syncs:
                continue
            for sync in plan_syncs:
                if not sync.sync_budget_line_id or sync.synced:
                    continue
                vals = {}
                vals['fiscalyear_id'] = sync.fiscalyear_id.id
                vals['activity_group_id'] = sync.activity_group_id.id
                vals['released_amount'] = sync.released_amount
                for i in range(1, 13):
                    vals['m' + str(i)] = sync['m' + str(i)]
                sync.sync_budget_line_id.write(vals)
                # Mark synced
                sync.write({'synced': True,
                            'last_sync': fields.Datetime.now()})
        return True

    @api.multi
    def action_sync_project_plan_to_budget_line(self):
        return self.sync_project_plan_to_budget_line(fiscalyear_ids=False)

    @api.multi
    def action_open_budget_control(self):
        self.ensure_one()
        # TODO: check for access?
        # self.env['res.invest.construction']._check_cooperate_access()
        action = self.env.ref('pabi_chartfield.'
                              'act_account_budget_view_project_base')
        result = action.read()[0]
        budgets = self.find_active_project_budget(self.fiscalyear_ids.ids,
                                                  [self.program_id.id])
        dom = [('id', 'in', budgets.ids)]
        result.update({'domain': dom})
        return result

    @api.multi
    def action_open_to_sync_budget_control(self):
        self.ensure_one()
        # TODO: check for access?
        # self.env['res.invest.construction']._check_cooperate_access()
        action = self.env.ref('pabi_chartfield.'
                              'act_account_budget_view_project_base')
        result = action.read()[0]
        to_sync_fiscals = self.budget_plan_ids.filtered(
            lambda l: not l.synced).mapped('fiscalyear_id')
        budgets = self.find_active_project_budget(to_sync_fiscals.ids,
                                                  [self.program_id.id])
        dom = [('id', 'in', budgets.ids)]
        result.update({'domain': dom})
        return result

    @api.multi
    @api.constrains('budget_plan_ids')
    def _trigger_auto_sync(self):
        for project in self:
            to_sync_fiscals = project.budget_plan_ids.filtered(
                lambda l: not l.synced).mapped('fiscalyear_id')
            budgets = self.find_active_project_budget(to_sync_fiscals.ids,
                                                      [project.program_id.id])
            for budget in budgets:
                if budget.project_auto_sync:
                    budget.with_context(
                        project_id=project.id).sync_budget_my_project()

    @api.multi
    def _release_fiscal_budget(self, fiscalyear, released_amount):
        """ Distribute budget released to all AG of the same year
            by distribute to the first AG first,
            show warning if released amount > planned amout
        """
        for project in self:
            budget_plans = project.budget_plan_ids.\
                filtered(lambda l: l.fiscalyear_id == fiscalyear)
            if not budget_plans:
                raise ValidationError(
                    _('Not allow to release budget for project without plan!'))
            planned_amount = sum([x.planned_amount for x in budget_plans])
            if released_amount > planned_amount:
                raise ValidationError(
                    _('Releasing budget > planned!'))
            budget_plans.write({'released_amount': 0.0})  # Set zero
            remaining = released_amount
            update_vals = []
            for budget_plan in budget_plans:
                if remaining > budget_plan.planned_amount:
                    update = {'released_amount': budget_plan.planned_amount}
                    remaining -= budget_plan.planned_amount
                    update_vals.append((1, budget_plan.id, update))
                else:
                    update = {'released_amount': remaining}
                    remaining = 0.0
                    update_vals.append((1, budget_plan.id, update))
                    break
            if update_vals:
                project.write({'budget_plan_ids': update_vals})
        return True

    @api.multi
    def write(self, vals):
        res = super(ResProject, self).write(vals)
        # If project group is changes, resync everything
        self.refresh_budget_line(vals)
        # Auto create fiscal plan line (for ease of use of user)
        self.prepare_fiscal_plan_line(vals)
        return res

    @api.multi
    def refresh_budget_line(self, vals):
        if 'project_group_id' in vals:
            for proj in self:
                # Delete all existing budget lines from this project
                proj.budget_plan_ids.mapped('sync_budget_line_id').unlink()
                # Find new budgets for this project
                budgets = self.find_active_project_budget(
                    proj.fiscalyear_ids.ids, [proj.program_id.id])
                budgets.sync_budget_my_project()

    @api.multi
    def prepare_fiscal_plan_line(self, vals):
        if ('date_start' in vals and vals.get('date_start')) or \
                ('date_end' in vals and vals.get('date_end')):
            Fiscal = self.env['account.fiscalyear']
            for proj in self:
                proj_fiscals = proj.budget_plan_ids.mapped('fiscalyear_id')
                fiscals = Fiscal.search([('date_start', '<=', proj.date_end),
                                         ('date_stop', '>=', proj.date_start)])
                fiscals -= proj_fiscals
                plan_lines = []
                for fiscal in fiscals:
                    plan_lines.append((0, 0, {'fiscalyear_id': fiscal.id}))
                proj.write({'budget_plan_ids': plan_lines})


class ResProjectMember(models.Model):
    _name = 'res.project.member'
    _description = 'Project Member'

    project_id = fields.Many2one(
        'res.project',
        string='Project',
        required=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )
    project_position = fields.Selection([
        ('manager', "Project Manager"),
        ('member', "Member"), ],
        string='Position',
        required=True,
    )

    @api.one
    @api.constrains('project_id', 'employee_id', 'project_position')
    def _check_unique_project_manager(self):
        self._cr.execute("""
            select coalesce(count(*))
            from res_project_member
            where project_position = 'manager'
            and project_id = %s
        """, (self.project_id.id,))
        count = self._cr.fetchone()[0]
        if count > 1:
            raise ValidationError(
                _('There are project with > 1 project manager'))


class ResProjectBudgetPlan(models.Model):
    _name = 'res.project.budget.plan'
    _description = 'Project Budget Lines and Released Amount'
    _order = 'fiscalyear_id, id'

    project_id = fields.Many2one(
        'res.project',
        string='Project',
        index=True,
        ondelete='cascade',
        readonly=True,
    )
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='Fiscalyear',
        required=True,
    )
    activity_group_id = fields.Many2one(
        'account.activity.group',
        string='Activity Group',
    )
    m1 = fields.Float(
        string='Oct',
        default=0.0,
    )
    m2 = fields.Float(
        string='Nov',
        default=0.0,
    )
    m3 = fields.Float(
        string='Dec',
        default=0.0,
    )
    m4 = fields.Float(
        string='Jan',
        default=0.0,
    )
    m5 = fields.Float(
        string='Feb',
        default=0.0,
    )
    m6 = fields.Float(
        string='Mar',
        default=0.0,
    )
    m7 = fields.Float(
        string='Apr',
        default=0.0,
    )
    m8 = fields.Float(
        string='May',
        default=0.0,
    )
    m9 = fields.Float(
        string='Jun',
        default=0.0,
    )
    m10 = fields.Float(
        string='Jul',
        default=0.0,
    )
    m11 = fields.Float(
        string='Aug',
        default=0.0,
    )
    m12 = fields.Float(
        string='Sep',
        default=0.0,
    )
    planned_amount = fields.Float(
        string='Planned Amount',
        compute='_compute_planned_amount',
        store=True,
    )
    released_amount = fields.Float(
        string='Released Amount',
        default=0.0,
    )
    # Sync information
    sync_budget_line_id = fields.Many2one(
        'account.budget.line',
        string='Budget Line Ref',
        index=True,
        ondelete='set null',
        help="This is of latest version of fiscalyear's budget control",
    )
    budget_id = fields.Many2one(
        'account.budget',
        related='sync_budget_line_id.budget_id',
        string='Budget Control',
        store=True,
        readonly=True,
    )
    last_sync = fields.Datetime(
        string='Last Sync',
        help="Latest syncing date/time",
    )
    synced = fields.Boolean(
        string='Synced',
        default=False,
        help="Checked when it is synced. Unchecked when plan is updated"
        "then it will be synced again",
    )

    @api.multi
    @api.depends('m1', 'm2', 'm3', 'm4', 'm5', 'm6',
                 'm7', 'm8', 'm9', 'm10', 'm11', 'm12',)
    def _compute_planned_amount(self):
        for rec in self:
            planned_amount = sum([rec.m1, rec.m2, rec.m3, rec.m4,
                                  rec.m5, rec.m6, rec.m7, rec.m8,
                                  rec.m9, rec.m10, rec.m11, rec.m12
                                  ])
            rec.planned_amount = planned_amount

    @api.multi
    def write(self, vals):
        changes = vals.keys()
        test_keys = ['m1', 'm2', 'm3', 'm4', 'm5', 'm6',
                     'm7', 'm8', 'm9', 'm10', 'm11', 'm12',
                     'fiscalyear_id', 'activity_group_id', 'released_amount']
        # If budget line table is changed at least 1 field, mark synced = False
        if len(set(changes).intersection(test_keys)) > 0:
            vals.update({'synced': False})  # Line updated
        return super(ResProjectBudgetPlan, self).write(vals)

    @api.multi
    def unlink(self):
        """ As the line is deleted, also delete the related budget control """
        self.mapped('sync_budget_line_id').unlink()
        return super(ResProjectBudgetPlan, self).unlink()


class ResProjectBudgetSummary(models.Model):
    _name = 'res.project.budget.summary'
    _auto = False
    _rec_name = 'fiscalyear_id'
    _description = 'Fiscal Year summary of each phase amount'

    project_id = fields.Many2one(
        'res.project',
        string='Project',
        readonly=True,
    )
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='fiscalyear',
        readonly=True,
    )
    planned_amount = fields.Float(
        string='Planned Amount',
        readonly=True,
    )
    released_amount = fields.Float(
        string='Released Amount',
        readonly=True,
    )

    def init(self, cr):

        _sql = """
            select min(id) as id, project_id, fiscalyear_id,
                sum(m1+m2+m3+m4+m5+m6+m7+m8+m9+m10+m11+m12) as planned_amount,
                sum(released_amount) as released_amount
            from res_project_budget_plan
            group by project_id, fiscalyear_id
        """

        tools.drop_view_if_exists(cr, self._table)
        cr.execute(
            """CREATE or REPLACE VIEW %s as (%s)""" %
            (self._table, _sql,))


class ResProjectBudgetRelease(models.Model):
    _name = 'res.project.budget.release'
    _description = 'History of budget release (interface with myProject)'

    fiscalyear_id = fields.Many2one(
        'account.fiscalyear',
        string='Fiscalyear',
        required=True,
    )
    project_id = fields.Many2one(
        'res.project',
        string='Project',
        required=True,
    )
    dummy_project_id = fields.Many2one(
        related='project_id',
        help="Dummy project_id, used to calculate init amount release",
    )
    released_amount = fields.Float(
        string='Released Amount',
        default=0.0,
        required=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True,
        required=True,
    )
    write_date = fields.Datetime(
        readonly=True,
    )

    @api.onchange('fiscalyear_id', 'project_id')
    def _onchange_project_fiscal(self):
        BudgetSummary = self.env['res.project.budget.summary']
        project_id = \
            self._context.get('project_id', False) or self.project_id.id
        summary = BudgetSummary.search([
            ('project_id', '=', project_id),
            ('fiscalyear_id', '=', self.fiscalyear_id.id)])
        self.released_amount = summary and summary[0].released_amount or 0.0

    @api.model
    def create(self, vals):
        rec = super(ResProjectBudgetRelease, self).create(vals)
        if 'released_amount' in vals:
            rec.project_id._release_fiscal_budget(rec.fiscalyear_id,
                                                  rec.released_amount)
        return rec

    @api.multi
    def write(self, vals):
        result = super(ResProjectBudgetRelease, self).write(vals)
        if 'released_amount' in vals:
            for rec in self:
                rec.project_id._release_fiscal_budget(rec.fiscalyear_id,
                                                      rec.released_amount)
        return result
