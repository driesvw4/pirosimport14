import logging
from odoo import models, fields, api, exceptions, tools

_logger = logging.getLogger(__name__)


class EuroclearCandidate(models.Model):
    _name = 'euroclear.candidate'
    _description = 'Euroclear candidate'

    name = fields.Char(string='Candidate')
    x_euroclear_candidate_donotpropose = fields.Boolean(string='Do Not Propose')
    x_euroclear_candidate_proposal = fields.One2many(
        'euroclear.proposal',
        'x_euroclear_proposal_candidate',
        string='Proposals',
    )


class EuroclearAmIintermediate(models.Model):
    _name = 'euroclear.am_im'
    _description = 'Euroclear am_im'
    name = fields.Char(string='AM Intermediate')


class EuroclearRole(models.Model):
    _name = 'euroclear.function'
    _description = 'Euroclear Function'
    x_euroclear_function_id = fields.Char(string='Function ID')
    name = fields.Char(string='Function')
    x_euroclear_function_link = fields.Html(string='Function Link')


class EuroclearSubcontractor(models.Model):
    _name = 'euroclear.subcontractor'
    _description = 'Euroclear subcontractor'
    name = fields.Char(string='Via')


class EuroclearEndcustomer(models.Model):
    _name = 'euroclear.endcustomer'
    _description = 'Euroclear endcustomer'
    name = fields.Char(string='End Customer')


class EuroclearProposal(models.Model):
    _name = 'euroclear.proposal'
    _inherit = 'euroclear.candidate'
    _description = 'Euroclear proposal'
    _order = "x_euroclear_proposal_date DESC"
    x_euroclear_proposal_date = fields.Date(string='Date')
    x_euroclear_proposal_endcustomer = fields.Many2one(
        comodel_name='euroclear.endcustomer',
        string='End Customer',
    )
    x_euroclear_proposal_role = fields.Many2one(
        comodel_name='euroclear.function',
        string='Role',
    )
    x_euroclear_proposal_candidate = fields.Many2one(
        comodel_name='euroclear.candidate',
        string='Candidate',
    )
    x_euroclear_proposal_via = fields.Many2one(
        comodel_name='euroclear.subcontractor',
        string='Via'
    )
    x_euroclear_proposal_cost = fields.Integer(string='Cost')
    x_euroclear_proposal_price = fields.Integer(string='Price Euroclear')
    x_euroclear_margin = fields.Integer(string='Margin', compute='compute_margin', store=True)
    x_euroclear_margin_pt = fields.Float(string='Margin %', compute='compute_margin', store=True)
    user_id = fields.Many2one('res.users', string='AM',
                              readonly=True, default=lambda self: self.env.user)
    x_euroclear_am_intermediate = fields.Many2one(
        comodel_name='euroclear.am_im',
        string='AM intermediate',
    )
    x_euroclear_proposal_feedback = fields.Text(string='Feedback')

    @api.onchange('x_euroclear_proposal_candidate')
    def onchange_tracking(self):
        if self.x_euroclear_proposal_candidate.name:
            self._cr.execute(
                'SELECT x_euroclear_candidate_donotpropose FROM euroclear_candidate WHERE name=%s and x_euroclear_candidate_donotpropose',
                (self.x_euroclear_proposal_candidate.name,))
            if self._cr.fetchone():
                return {
                    'warning': {
                        'title': ('Warning!'),
                        'message': ("The candidate should not be proposed anymore")
                    }
                }

    @api.depends('x_euroclear_proposal_price', 'x_euroclear_proposal_cost')
    def compute_margin(self):
        for line in self:
            sprice = line.x_euroclear_proposal_price
            pprice = line.x_euroclear_proposal_cost
            margin = sprice - pprice
            if sprice:
                margin_pt = (sprice - pprice) / sprice * 100
            else:
                margin_pt = 0
            line.update({
                'x_euroclear_margin': margin,
                'x_euroclear_margin_pt': margin_pt,
            })


class EuroclearCandidateProposedFunctions(models.Model):
    _name = 'euroclear.candidateproposedfunctions'
    _description = 'Euroclear candidateproposedfunctions'

    _auto = False
    x_euroclear_candidateproposedfunctions_date = fields.Date()
    x_euroclear_candidateproposedfunctions_function = fields.Char()
    x_euroclear_candidateproposedfunctions_feedback = fields.Text()
    x_euroclear_candidateproposedfunctions_candidate = fields.Many2one(
        comodel_name='euroclear.candidate',
        string='Candidate',
    )

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE VIEW %s AS (
                SELECT 
                euroclear_proposal.id as id,
                x_euroclear_proposal_date as x_euroclear_candidateproposedfunctions_date, 
                euroclear_function.name as x_euroclear_candidateproposedfunctions_function, 
                x_euroclear_proposal_feedback as x_euroclear_candidateproposedfunctions_feedback,
                euroclear_candidate.id as x_euroclear_candidateproposedfunctions_candidate
                FROM euroclear_proposal 
                LEFT JOIN euroclear_function on euroclear_proposal.x_euroclear_proposal_role = euroclear_function.id 
                LEFT JOIN euroclear_candidate on euroclear_proposal.x_euroclear_proposal_candidate = euroclear_candidate.id
                WHERE x_euroclear_proposal_candidate=1345
            )""" % (self._table))
        # return {
        #    'warning': {
        #        'title': ('Warning!'),
        #        'message': (self._table)
        #    }
        # }
        _logger.debug("BLOSSOM " + self._table)
#        _logger.debug("BLOSSOM " + self.x_euroclear_candidateproposedfunctions_candidate.name)
