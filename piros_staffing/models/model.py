import logging
from odoo import models, fields, api, exceptions, tools

_logger = logging.getLogger(__name__)

class PirosStaffingCandidate(models.Model):
    _name = 'piros_staffing.candidate'
    name = fields.Char(string='Candidate')
    x_piros_staffing_candidate_donotpropose = fields.Boolean(string='Do Not Propose')
    x_piros_staffing_candidate_proposal = fields.One2many(
            'piros_staffing.proposal',
            'x_piros_staffing_proposal_candidate',
            string='Proposals',
    )

class PirosStaffingAmIintermediate(models.Model):
    _name = 'piros_staffing.am_im'
    name = fields.Char(string='AM Intermediate')



class PirosStaffingRole(models.Model):
    _name = 'piros_staffing.function'
    x_piros_staffing_function_id = fields.Char(string='Function ID')
    name = fields.Char(string='Function')
    x_piros_staffing_function_link = fields.Html(string='Function Link')

class PirosStaffingSubcontractor(models.Model):
    _name = 'piros_staffing.subcontractor'
    name = fields.Char(string='Via')

class PirosStaffingEndcustomer(models.Model):
    _name = 'piros_staffing.endcustomer'
    name = fields.Char(string='End Customer')

class PirosStaffingProposal(models.Model):
    _name = 'piros_staffing.proposal'
    _inherit = 'piros_staffing.candidate'
    _order = "x_piros_staffing_proposal_date DESC"
    x_piros_staffing_proposal_date = fields.Date(string='Date')
    x_piros_staffing_proposal_endcustomer = fields.Many2one(
        comodel_name='res.partner',
        string='End Customer',
    )
    x_piros_staffing_proposal_role = fields.Many2one(
        comodel_name='piros_staffing.function',
        string='Role',
    )
    x_piros_staffing_proposal_candidate = fields.Many2one(
        comodel_name='hr.employee',
        string='Candidate',
    ) 
    x_piros_staffing_proposal_via = fields.Many2one(
            comodel_name='res.partner',
            string='Via'
    )
    x_piros_staffing_proposal_cost = fields.Float(string='Cost')
    x_piros_staffing_proposal_price = fields.Float(string='Price Proposed')
    x_piros_staffing_margin = fields.Integer(string='Margin', compute='compute_margin', store=True)
    x_piros_staffing_margin_pt = fields.Float(string='Margin %', compute='compute_margin', store=True)
    user_id = fields.Many2one('res.users', string='AM', track_visibility='onchange',
    readonly=True, default=lambda self: self.env.user)
    x_piros_staffing_am_intermediate = fields.Many2one(
            comodel_name='res.partner',
            string='AM intermediate',
    )
    x_piros_staffing_proposal_feedback = fields.Text(string='Feedback')

    @api.onchange('x_piros_staffing_proposal_candidate')
    def onchange_tracking(self):
        if self.x_piros_staffing_proposal_candidate.name:
          self._cr.execute('SELECT x_piros_staffing_candidate_donotpropose FROM piros_staffing_candidate WHERE name=%s and x_piros_staffing_candidate_donotpropose', (self.x_piros_staffing_proposal_candidate.name,))
          if self._cr.fetchone():
            return {
                    'warning': {
                        'title': ('Warning!'),
                        'message': ("The candidate should not be proposed anymore")
                    }
            }
          Obj=self.env['hr.employee'].search([('name', '=', self.x_piros_staffing_proposal_candidate.name)])
          get_cost = Obj[0].x_timesheet_cost
          self.x_piros_staffing_proposal_cost = get_cost

    @api.depends('x_piros_staffing_proposal_price','x_piros_staffing_proposal_cost')
    def compute_margin(self):
      for line in self:
        sprice = line.x_piros_staffing_proposal_price
        pprice = line.x_piros_staffing_proposal_cost
        margin = sprice - pprice
        if sprice:
          margin_pt = (sprice-pprice)/sprice*100
        else:
          margin_pt = 0
        line.update({
              'x_piros_staffing_margin': margin,
              'x_piros_staffing_margin_pt': margin_pt,
            })

class PirosStaffingCandidateProposedFunctions(models.Model):
    _name = 'piros_staffing.candidateproposedfunctions'
    _auto = False
    x_piros_staffing_candidateproposedfunctions_date = fields.Date()
    x_piros_staffing_candidateproposedfunctions_function = fields.Char()
    x_piros_staffing_candidateproposedfunctions_feedback = fields.Text()
    x_piros_staffing_candidateproposedfunctions_candidate = fields.Many2one(
        comodel_name='piros_staffing.candidate',
        string='Candidate',
    )

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                piros_staffing_proposal.id as id,
                x_piros_staffing_proposal_date as x_piros_staffing_candidateproposedfunctions_date, 
                piros_staffing_function.name as x_piros_staffing_candidateproposedfunctions_function, 
                x_piros_staffing_proposal_feedback as x_piros_staffing_candidateproposedfunctions_feedback,
                piros_staffing_candidate.id as x_piros_staffing_candidateproposedfunctions_candidate
                FROM piros_staffing_proposal 
                LEFT JOIN piros_staffing_function on piros_staffing_proposal.x_piros_staffing_proposal_role = piros_staffing_function.id 
                LEFT JOIN piros_staffing_candidate on piros_staffing_proposal.x_piros_staffing_proposal_candidate = piros_staffing_candidate.id
                WHERE x_piros_staffing_proposal_candidate=1345
            )""" % (self._table))
        #return {
        #    'warning': {
        #        'title': ('Warning!'),
        #        'message': (self._table)
        #    }
        #}
        _logger.debug("BLOSSOM " + self._table)
#        _logger.debug("BLOSSOM " + self.x_piros_staffing_candidateproposedfunctions_candidate.name)

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'
    currency_id = fields.Many2one(
        'res.currency', string='Currency')
    x_timesheet_cost = fields.Monetary(currency_field='currency_id',string='Cost')
