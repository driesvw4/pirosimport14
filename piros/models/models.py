# -*- coding: utf-8 -*-

from odoo import tools, models, fields, api, registry, _
from odoo.exceptions import UserError

import re


class SalesExtension(models.Model):
    _inherit = 'sale.order'

    x_end_customer_id = fields.Many2one('res.partner', string='End Customer', required=True)
    x_marginsplit_id = fields.Many2one('piros.marginsplit', string='Margin Split', required=False)

    x_totalcost = fields.Monetary(compute='_compute_totalcost', store=True, string='Purchase Price')
    x_pirosmargin = fields.Monetary(compute='_compute_margin', store=True, string='Piros Margin')
    x_pirosmargin_pct = fields.Float(compute='_compute_margin_pct', store=True, string='Piros Margin %')
    x_totalintercompany = fields.Monetary(compute='_compute_totalintercompany', store=True, string='Total Intercompany')

    x_startdate = fields.Date(string="Start Date", store=True, compute='_compute_startdate')
    x_enddate = fields.Date(string="End Date", store=True, compute='_compute_enddate')
    x_renewal = fields.Char(string='New/Renewal', store=True, compute='_compute_renewal')
    x_types = fields.Char(string='Type', store=True, compute='_compute_types')
    x_summary = fields.Char(string='Summary', store=True, compute='_compute_summary')
    x_syb = fields.Monetary(string='SYB', store=True, compute='_compute_syb')
    x_co_term = fields.Boolean(string='Co-Term', store=True, compute='_compute_co_term')

    @api.depends('order_line.x_startdate')
    def _compute_startdate(self):
        for order in self:
            first = None
            for line in order.order_line:
                if line.x_startdate:
                    if first is None or line.x_startdate < first:
                        first = line.x_startdate
            order.update(dict(x_startdate=first))

    @api.depends('order_line.x_enddate')
    def _compute_enddate(self):
        for order in self:
            last = None
            for line in order.order_line:
                if line.x_enddate:
                    if last is None or line.x_enddate > last:
                        last = line.x_enddate
            order.update(dict(x_enddate=last))

    @api.depends('order_line.x_renewal')
    def _compute_renewal(self):
        for order in self:
            types = set()
            for line in order.order_line:
                types.add(line.x_renewal)
            order.update(dict(x_renewal=', '.join([t for t in types if t])))

    @api.depends('order_line.product_id.type')
    def _compute_types(self):
        for order in self:
            types = set()
            for line in order.order_line:
                types.add(line.product_id.product_tmpl_id.type)
            order.update(dict(x_types=', '.join([t for t in types if t])))

    @api.depends('order_line.product_id.categ_id.name')
    def _compute_summary(self):
        for order in self:
            categories = set()
            for line in order.order_line:
                categories.add(line.product_id.categ_id.name)
            order.update(dict(x_summary=', '.join(categories)))

    @api.depends('x_marginsplit_id', 'partner_id.x_marginsplit_id', 'order_line.x_enddate', 'order_line.x_startdate',
                 'order_line.purchase_price', 'order_line.price_subtotal')
    def _compute_syb(self):
        for order in self:
            marginsplit = order.x_marginsplit_id or order.partner_id.x_marginsplit_id
            syb = 0.0
            for line in order.order_line:
                piros_margin = SalesExtension.calculate_piros_margin(line.purchase_price, line.price_subtotal,
                                                                     marginsplit)
                piros_revenue = line.purchase_price + piros_margin

                if not line.x_startdate or not line.x_enddate:
                    syb += piros_revenue

                if line.x_startdate and line.x_enddate:
                    years = line.x_enddate.year - line.x_startdate.year
                    if years < 2:
                        syb += piros_revenue
                    else:
                        syb += piros_revenue / years
            order.update(dict(x_syb=syb))

    # @api.depends('order_line.x_enddate', 'order_line.x_startdate')
    def _compute_co_term(self):
        for order in self:
            start_dates = set()
            end_dates = set()
            # years_set = set()
            months_set = set()

            # Scan over all order lines to keep track of the start and end dates, and their difference in years
            # (At least 1 year)
            for line in order.order_line:
                if not line.x_startdate or not line.x_enddate:
                    continue
                start_dates.add(line.x_startdate)
                end_dates.add(line.x_enddate)
                #    years = line.x_enddate.year - line.x_startdate.year
                months = (
                                     line.x_enddate.year - line.x_startdate.year) * 12 + line.x_enddate.month - line.x_startdate.month
                #    if years < 2:
                #        years = 1
                #    years_set.add(years)
                months_set.add(months)

            # First, we assume we are not co-term
            is_co_term = False

            # We will check in all order lines, if there is one that is not in a 1/3/5 scheme.
            # for years in years_set:
            #    if years not in [1, 3, 5]:
            #        is_co_term = True
            #        break
            for months in months_set:
                if months not in [12, 36, 60]:
                    is_co_term = True
                    break

            # If we still are not co-term after the test above, we will check if we have only one unique end date,
            # and multiple different start dates.
            if not is_co_term:
                if len(end_dates) == 1 and len(start_dates) > 1:
                    is_co_term = True

            # Update the record accordingly.
            order.update(dict(x_co_term=is_co_term))

    @staticmethod
    def calculate_piros_margin(purchase, sale, marginsplit=None):
        gross_margin = sale - purchase
        piros_margin = gross_margin

        if not marginsplit:
            return piros_margin

        if marginsplit.x_kind == 'fixed':
            piros_margin = marginsplit.x_fixed_price

        elif marginsplit.x_kind == 'total_percentage':
            inter_company_margin = sale * marginsplit.x_percentage_ep / 100
            piros_margin = gross_margin - inter_company_margin

        elif marginsplit.x_kind == 'split_percentage':
            piros_margin = gross_margin * marginsplit.x_percentage_split / 100

        elif marginsplit.x_kind == 'total_percentage_split':
            piros_margin = ((sale - (sale * marginsplit.x_percentage_ep / 100)) - purchase) * (
                        marginsplit.x_percentage_split / 100)
            inter_company_margin = gross_margin - piros_margin

        return piros_margin

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        """
        This is an undocumented feature of Odoo. We don't want the SaleOrder.message_post method to execute, we want to
        go directly to its parent. Because we cannot import Odoo model classed directly, we make use of the global
        model registry to retrieve the MailThread class, which contains the correct message_post method that we want to
        use.
        """
        MailThread = registry().get('mail.thread')

        # Same as SaleOrder.message_post
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state == 'draft').with_context(tracking_disable=True).write({'state': 'sent'})
            self.env.company.sudo().set_onboarding_step_done('sale_onboarding_sample_quotation_state')

        # This is the clue: we don't want to add recipients automatically as followers.
        return super(MailThread, self.with_context(mail_post_autofollow=False)).message_post(**kwargs)

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        self.write({
            'state': 'sale',
            'date_order': fields.Datetime.now()
        })
        self._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        return True

    def _find_mail_template(self, force_confirmation_template=False):
        if self.env.context.get('proforma', False):
            return self.env['ir.model.data'].xmlid_to_res_id('piros.piros_send_to_billing', raise_if_not_found=False)

        super()._find_mail_template(force_confirmation_template=force_confirmation_template)

    @api.depends('order_line.purchase_price', 'order_line.product_uom_qty')
    def _compute_totalcost(self):
        for order in self:
            totalcost = sum([line.purchase_price * line.product_uom_qty for line in order.order_line])
            order.update(dict(x_totalcost=totalcost))

    @api.depends('order_line.purchase_price', 'order_line.product_uom_qty', 'x_marginsplit_id',
                 'amount_untaxed', 'x_totalcost')
    def _compute_margin(self):
        for order in self:
            totalcost = sum([line.purchase_price * line.product_uom_qty for line in order.order_line])
            end_user_price = order.amount_untaxed
            marginsplit = order.x_marginsplit_id or order.partner_id.x_marginsplit_id

            if not marginsplit:
                order.update({'x_pirosmargin': order.margin})
                continue

            piros_margin = SalesExtension.calculate_piros_margin(totalcost, end_user_price, marginsplit)

            order.update({'x_pirosmargin': piros_margin})

    @api.depends('x_pirosmargin', 'amount_untaxed')
    def _compute_margin_pct(self):
        for order in self:
            if order.amount_untaxed == 0.0:
                percent = 0.0
            else:
                percent = order.x_pirosmargin * 100 / order.amount_untaxed
            order.update(dict(x_pirosmargin_pct=percent))

    @api.depends('x_pirosmargin', 'x_totalcost')
    def _compute_totalintercompany(self):
        for order in self:
            total = order.x_totalcost + order.x_pirosmargin
            order.update(dict(x_totalintercompany=total))


class SalesLineExtension(models.Model):
    _inherit = 'sale.order.line'

    x_startdate = fields.Date(string="Start Date")
    x_enddate = fields.Date(string="End Date")
    x_contract = fields.Integer(string="Contract #")
    x_renewal = fields.Selection([
        ('new', 'New'),
        ('renewal', 'Renewal')], string='Type')
    x_discountedprice = fields.Monetary(compute='_compute_discountedprice', store='true',
                                        string='Discounted Unit Price')

    @api.depends('discount', 'price_unit')
    def _compute_discountedprice(self):
        for line in self:
            line.x_discountedprice = line.price_unit * (1 - (line.discount / 100))

    def humanize_quantity(self):
        return re.sub(r'\.0+', '', str(self.product_uom_qty))


class RenewalsOverview(models.Model):
    _name = 'piros.renewals.overview'
    _description = 'piros renewals overview'
    _auto = False

    x_date = fields.Date('Date')
    x_so = fields.Char('SO')
    x_customer = fields.Char('Customer')
    x_end_customer = fields.Char('End Customer')
    x_product = fields.Char('Product')
    x_qty = fields.Float('Qty')
    x_contract = fields.Integer(string="Contract #")
    x_order_id = fields.Integer(string="ID")

    #  @api.model_cr
    def init(self):
        print("Connected")
        tools.drop_view_if_exists(self.env.cr, 'piros_renewals_overview')
        self.env.cr.execute("""
          CREATE OR REPLACE VIEW piros_renewals_overview AS (
            SELECT 
            row_number() OVER () as id,
            sale_order_line.x_enddate as x_date, 
            sale_order.name as x_so, 
            sale_order.id as x_order_id,
            rp1.commercial_company_name as x_customer, 
            rp2.commercial_company_name as x_end_customer, 
            sale_order_line.name as x_product, 
            sale_order_line.product_uom_qty as x_qty, 
            sale_order_line.x_contract as x_contract 
            FROM sale_order_line 
            JOIN sale_order ON sale_order_line.order_id = sale_order.id  
            JOIN res_partner rp1 ON sale_order.partner_id = rp1.id 
            JOIN res_partner rp2 ON sale_order.x_end_customer_id = rp2.id 
            WHERE sale_order.state = 'sale'
            GROUP BY sale_order_line.x_enddate,sale_order.id,sale_order.name,rp1.commercial_company_name,rp2.commercial_company_name,sale_order_line.name,sale_order_line.product_uom_qty,sale_order_line.x_contract 
            ORDER BY x_date
          )""")

    def button_so(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': int(self.x_order_id),
            'type': 'ir.actions.act_window',
        }


class MarginSplit(models.Model):
    _name = 'piros.marginsplit'
    _rec_name = 'x_name'
    _description = 'piros marginsplit'

    x_name = fields.Char('Name')
    x_kind = fields.Selection(
        selection=[
            ('total_percentage', 'Total percent'),
            ('fixed', 'Fixed'),
            ('split_percentage', 'Split percent'),
            ('total_percentage_split', 'Split after total percent'),
        ],
        string='Kind'
    )
    x_percentage_ep = fields.Float('Percentage EP', required=False)
    x_percentage_split = fields.Float('Percentage Split', required=False)
    x_fixed_price = fields.Float('Fixed Price', required=False, digits=(12, 2))


# class LicenseProduct(models.Model):
#    _inherit = "product.product"
#
#    type = fields.Selection([
#        ('license', 'License'),
#        ('consu', 'Consumable'),
#        ('sub', 'Subscription'),
#        ('service', 'Service')], string='Product Type', default='license', required=True,
#        help='A license product is a product designed for Software Licenses\n'
#             'A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
#             'A consumable product is a product for which stock is not managed.\n'
#             'A service is a non-material product you provide.')
# .
#    @api.onchange('type')
#    def _onchange_type(self):
#        super()._onchange_type()
#        if self.type == 'service':
#            self.invoice_policy = 'order'
#            self.service_type = 'timesheet'
#        elif self.type == 'consu' and self.service_policy == 'ordered_timesheet':
#            self.invoice_policy = 'order'
#        elif self.type in ('license', 'sub'):
#            self.invoice_policy = 'order'


class LicenseProductTemplate(models.Model):
    _inherit = "product.template"

    type = fields.Selection([
        ('license', 'License'),
        ('consu', 'Consumable'),
        ('sub', 'Subscription'),
        ('service', 'Service'),
        ('product', 'Storable Product')], string='Product Type', default='license', required=True,
        help='A license product is a product designed for Software Licenses\n'
             'A storable product is a product for which you manage stock. The Inventory app has to be installed.\n'
             'A consumable product is a product for which stock is not managed.\n'
             'A service is a non-material product you provide.')

    @api.onchange('type')
    def _onchange_type(self):
        super()._onchange_type()
        if self.type == 'service':
            self.invoice_policy = 'order'
            # self.service_type = 'timesheet'
        # elif self.type == 'consu' and self.service_policy == 'ordered_timesheet':
        elif self.type == 'consu':
            self.invoice_policy = 'order'
        elif self.type in ('license', 'sub'):
            self.invoice_policy = 'order'


class PurchaseExtension(models.Model):
    _inherit = 'purchase.order'

    x_end_customer_id = fields.Many2one('res.partner', string='End Customer', required=True)
    x_marginsplit_id = fields.Many2one('piros.marginsplit', string='Margin Split', required=False)


class PurchaseLineExtension(models.Model):
    _inherit = 'purchase.order.line'

    x_startdate = fields.Date(string="Start Date")
    x_enddate = fields.Date(string="End Date")
    x_contract = fields.Integer(string="Contract #")
    x_renewal = fields.Selection([
        ('new', 'New'),
        ('renewal', 'Renewal')], string='Type')
    x_discount = fields.Float(digits=(6, 2), string='Purchase Discount %')
    x_discountedprice = fields.Monetary(compute='_compute_discountedprice', store='true',
                                        string='Purchase Unit Price')

    @api.depends('x_discount', 'price_unit')
    def _compute_discountedprice(self):
        for line in self:
            line.x_discountedprice = line.price_unit * (1 - (line.x_discount / 100))

    @api.depends('product_qty', 'taxes_id', 'x_discountedprice')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                line.x_discountedprice,
                vals['currency_id'],
                vals['product_qty'],
                vals['product'],
                vals['partner'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def humanize_quantity(self):
        return re.sub(r'\.0+', '', str(self.product_qty))


class PartnerExtension(models.Model):
    _inherit = 'res.partner'

    x_marginsplit_id = fields.Many2one('piros.marginsplit', string='Margin Split', required=False)
    x_intercompany = fields.Boolean(default=False, string='Is Cronos Intercompany')
    x_redhat_accountmanager = fields.Many2one('res.partner', string='Red Hat Account Manager', required=False)
    x_redhat_internalsales = fields.Many2one('res.partner', string='Red Hat Internal Sales', required=False)
    x_indirect_sale_order_count = fields.Integer(compute='_compute_indirect_sale_order_count',
                                                 string='Indirect Sale Order Count')
    x_partner_attachment_ids = fields.Many2many('ir.attachment', 'res_id', string='Documents')

    # x_partner_tags = fields.Many2many('res.partner.category', string='Tags')

    def _compute_indirect_sale_order_count(self):
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])

        sale_order_groups = self.env['sale.order'].read_group(
            domain=[('x_end_customer_id', 'in', all_partners.ids), ('partner_id', 'not in', all_partners.ids)],
            fields=['x_end_customer_id'], groupby=['x_end_customer_id']
        )
        partners = self.browse()
        for group in sale_order_groups:
            partner = self.browse(group['x_end_customer_id'][0])
            while partner:
                if partner in self:
                    partner.x_indirect_sale_order_count += group['x_end_customer_id_count']
                    partners |= partner
                partner = partner.parent_id
        (self - partners).x_indirect_sale_order_count = 0
