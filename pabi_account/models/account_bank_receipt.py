# -*- coding: utf-8 -*-

from openerp import models, fields, api


class AccountBankReceipt(models.Model):
    _inherit = "account.bank.receipt"

    partner_bank_id = fields.Many2one(
        'res.partner.bank',
        domain="[('partner_id', '=', company_partner_id),"
        "('state', '=', 'SA')]",
    )
    bank_account_id = fields.Many2one(
        'account.account',
        related=False,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    partner_bank_id_readonly = fields.Many2one(
        'res.partner.bank',
        related='partner_bank_id',
        string='Bank Account',
        readonly=True,
    )

    @api.onchange('bank_account_id')
    def onchange_bank_account_id(self):
        self.partner_bank_id = False
        if self.bank_account_id:
            Journal = self.env['account.journal']
            BankAcct = self.env['res.partner.bank']
            journals = Journal.search([('default_debit_account_id', '=',
                                        self.bank_account_id.id)])
            banks = BankAcct.search([('journal_id', 'in', journals.ids),
                                     ('state', '=', 'SA')])
            self.partner_bank_id = banks and banks[0] or False