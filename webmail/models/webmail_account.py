# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import socket
import imapclient
import imaplib

from odoo import _, fields, models
from odoo.exceptions import UserError

class WebmailAccount(models.Model):
    _name = "webmail.account"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Mail account"

    host = fields.Char(required=True)

    login = fields.Char(required=True)

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True
    )

    password = fields.Char(required=True)

    def button_test(self):
        client = self._get_client_connected()
        client.logout()

    def _get_client_connected(self):
        self.ensure_one()
        try:
            client = imapclient.IMAPClient(host=self.host)
        except socket.gaierror as e:
            raise UserError(_(
                "server '%s' has not been reached. Possible Reasons: \n"
                "- the server doesn't exist"
                "- your odoo instance faces to network issue"
            ) % (self.host))

        try:
            client.login(self.login, self.password)
        except imaplib.IMAP4.error as e:
            raise UserError(_(
                "Authentication failed. Possible Reasons: \n"
                "- your credentials are incorrect (%s // **********)"
            ) % (self.login))

        return client