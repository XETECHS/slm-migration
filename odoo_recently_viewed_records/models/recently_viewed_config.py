# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    recently_viewed_limit = fields.Integer("Recently Viewed Records Limit", help="Limit the Number of Recently Viewed Records.")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_default = self.env['ir.default'].sudo()
        ir_default.sudo().set('res.config.settings', 'recently_viewed_limit',self.recently_viewed_limit)
        return True

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_default = self.env['ir.default'].sudo()
        recently_viewed_limit = ir_default.get('res.config.settings', 'recently_viewed_limit')
        res.update({
            'recently_viewed_limit':recently_viewed_limit,
        })
        return res
