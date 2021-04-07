# -*- coding: utf-8 -*-
from odoo import http


class Piros(http.Controller):
    @http.route('/piros/marginsplit/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/piros/marginsplit/objects/', auth='public')
    def list(self, **kw):
        return http.request.render('piros.listing', {
            'root': '/piros/marginsplit',
            'objects': http.request.env['piros.marginsplit'].search([]),
        })

    @http.route('/piros/marginsplit/objects/<model("piros.marginsplit"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('piros.object', {
            'object': obj
        })
