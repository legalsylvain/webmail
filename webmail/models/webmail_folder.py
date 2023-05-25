# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import fields, models

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
        required=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="webmail_account_id.user_id",
        store=True,
        readonly=True,
    )

    technical_name = fields.Char()

    def _fetch_folders(self, webmail_account):
        client = webmail_account._get_client_connected()
        folder_datas = client.list_folders()
        client.logout()

        for folder_data in folder_datas:
            (_tags, separator, technical_name) = folder_data

            self._get_or_create(webmail_account, separator.decode(), technical_name)

    def _get_or_create(self, webmail_account, separator, technical_name):
        # Check if folder exist in Odoo
        existing_folder = self.search(
            [
                ("webmail_account_id", "=", webmail_account.id),
                ("technical_name", "=", technical_name),
            ]
        )
        if not existing_folder:
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
                            webmail_account, separator, "/".join(name_parts[:-1])
                        )
                    }
                )

            self.create(vals)
            _logger.info(
                "fetch from the upstream mail server."
                " Account %s. Creation of folder %s"
                % (webmail_account.name, vals["name"])
            )
