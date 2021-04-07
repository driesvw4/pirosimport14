# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class Euroclear_partner(models.Model):
    _name = 'euroclear.partner'
    _inherit = 'euroclear.partner'
