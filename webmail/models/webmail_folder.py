# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import re
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WebmailFolder(models.Model):
    _name = "webmail.folder"
    _description = "Webmail Folders"
    _order = "technical_name"

    name = fields.Char(required=True, readonly=True)

    parent_id = fields.Many2one(
        comodel_name="webmail.folder",
        readonly=True,
    )

    webmail_account_id = fields.Many2one(
        comodel_name="webmail.account",
        ondelete="cascade",
        required=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="webmail_account_id.user_id",
        store=True,
        readonly=True,
    )

    mail_ids = fields.One2many(
        comodel_name="webmail.mail",
        inverse_name="folder_id",
    )

    mail_qty = fields.Integer(compute="_compute_mail_qty", store=True)

    technical_name = fields.Char(required=True, readonly=True)

    # Compute Section
    @api.depends("mail_ids")
    def _compute_mail_qty(self):
        for folder in self:
            folder.mail_qty = len(folder.mail_ids)

    # Action Section
    def button_fetch_mails(self):
        for folder in self:
            self.env["webmail.mail"]._fetch_mails(folder)

    # Private Section
    def _fetch_folders(self, webmail_account):
        client = webmail_account._get_client_connected()
        status, folder_datas = client.list()
        client.logout()

        for folder_data in folder_datas:
            technical_name = folder_data.decode().split(' "/" ')[-1]
            if technical_name.startswith('"') and technical_name.endswith('"'):
                technical_name = technical_name[1:-1]

            self._get_or_create(webmail_account, technical_name)

    def _get_or_create(self, webmail_account, technical_name):
        separator = "/"
        # Check if folder exist in Odoo
        existing_folder = self.search(
            [
                ("webmail_account_id", "=", webmail_account.id),
                ("technical_name", "=", technical_name),
            ]
        )
        if existing_folder:
            return existing_folder

        name_parts = technical_name.split(separator)
        vals = {
            "webmail_account_id": webmail_account.id,
            "technical_name": technical_name,
            "name": name_parts[-1],
        }
        if separator in technical_name:
            vals.update(
                {
                    "parent_id": self._get_or_create(
                        webmail_account, separator.join(name_parts[:-1])
                    ).id
                }
            )

        _logger.debug(
            "fetch from the upstream mail server."
            " Account %s. Creation of folder %s" % (webmail_account.name, vals["name"])
        )
        return self.create(vals)
