# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import email
import hashlib
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"
    _order = "date desc"
    _rec_name = "subject"

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        ondelete="cascade",
        required=True,
        readonly=True,
    )

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    identifier = fields.Char(required=True, readonly=True)

    reply_identifier = fields.Char(readonly=True)

    origin_mail_id = fields.Many2one(
        comodel_name="webmail.mail", compute="_compute_origin_mail_id", store=True
    )
    data = fields.Text(readonly=True)

    # Extra Mail Fields
    date = fields.Datetime(required=True, readonly=True)

    subject = fields.Char(readonly=True)

    sender = fields.Char(readonly=True)

    body = fields.Html("Contents", readonly=True, sanitize_style=True)

    @api.depends("reply_identifier")
    def _compute_origin_mail_id(self):
        for mail in self:
            origin_mail = self.search([("identifier", "=", mail.reply_identifier)])
            mail.origin_mail_id = origin_mail.id

    # Overload Section
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for mail in records:
            other_mails = self.search([("reply_identifier", "=", mail.identifier)])
            if other_mails:
                other_mails.write({"origin_mail_id": mail.id})
        return records

    def _create_or_update_mail(self, webmail_folder, mail_data):
        email_message = email.message_from_bytes(mail_data, policy=email.policy.default)
        data = email_message.as_string()

        identifier = self._get_identifier_from_message(email_message, mail_data)
        message_dict = self.env["mail.thread"].message_parse(email_message)
        # Check if mail exists in Odoo
        existing_mail = self.search([("identifier", "=", identifier)])
        if existing_mail:
            # If mail exists, we just handle the use case where the mail
            # has moved from a folder to another, in the Mailbox.
            if existing_mail.folder_id != webmail_folder:
                existing_mail.write({"folder_id": webmail_folder.id})
            return existing_mail

        vals = {
            "identifier": identifier,
            "reply_identifier": email_message["In-Reply-To"],
            "date": message_dict["date"],
            "data": data,
            "folder_id": webmail_folder.id,
            "subject": message_dict["subject"],
            "sender": email_message["From"],
            "body": message_dict["body"],
        }

        _logger.debug(
            f"[FETCH] {webmail_folder.webmail_account_id.login} /"
            f" {webmail_folder.technical_name}:"
            f" Creation of mail {identifier}."
        )
        return self.create(vals)

    @api.model
    def _get_identifier_from_message(self, email_message, message_bytes):
        """Extract Message-ID field from message data.
        This field is like a unique ID for email systems.
        In rare case, this fields is not set. In that case,
        we generate a unique text, based on an hash of the email data."""
        identifier = email_message["Message-ID"]
        if not identifier:
            identifier = hashlib.sha256(message_bytes).hexdigest()
        return identifier
