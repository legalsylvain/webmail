# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import socket
import imapclient
import imaplib

from odoo import _, api, fields, models
from odoo.exceptions import UserError

class WebmailAccount(models.Model):
    _name = "webmail.account"
    _description = "Webmail Accounts"

    name = fields.Char(compute="_compute_name", store=True)

    host_id = fields.Many2one(comodel_name="webmail.host", required=True)

    host_url = fields.Char(related="host_id.url", store=True)

    login = fields.Char(required=True)

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True
    )

    password = fields.Char(required=True)

    @api.depends("login", "host_id.name")
    def _compute_name(self):
        for account in self:
            account.name = "%s (%s)" % (account.login, account.host_id.name)

    # Action Section
    def button_test_connexion(self):
        self.with_delay()._test_connexion()

    def button_fetch_folders(self):
        self.env["webmail.folder"].with_delay()._fetch_folders(self)

    # Private Section
    def _test_connexion(self):
        self.ensure_one()
        client = self._get_client_connected()
        client.logout()

    def _get_client_connected(self):
        self.ensure_one()
        try:
            client = imapclient.IMAPClient(host=self.host_url)
        except socket.gaierror as e:
            raise UserError(_(
                "server '%s' has not been reached. Possible Reasons: \n"
                "- the server doesn't exist"
                "- your odoo instance faces to network issue"
            ) % (self.host_url))

        try:
            client.login(self.login, self.password)
        except imaplib.IMAP4.error as e:
            raise UserError(_(
                "Authentication failed. Possible Reasons: \n"
                "- your credentials are incorrect (%s // **********)"
            ) % (self.login))

        return client