# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import imaplib
import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"
    _order = "date_mail desc"

    date_mail = fields.Datetime(required=True, readonly=True)

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        required=True,
        readonly=True,
    )

    identifier = fields.Char(required=True, readonly=True)

    origin_mail_id = fields.Many2one(comodel_name="webmail.mail", readonly=True)

    reply_identifier = fields.Char(readonly=True)

    subject = fields.Char(required=True, readonly=True)

    sender = fields.Char(required=True, readonly=True)

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    envelope_data = fields.Text(
        string="Technical field with all the envelope", readonly=True
    )

    def _fetch_mails(self, webmail_folder):
        client = webmail_folder.webmail_account_id._get_client_connected()
        try:
            client.select_folder(webmail_folder.technical_name)
        except imaplib.IMAP4.error as e:
            client.logout()
            raise UserError(
                _(
                    "Folder %(folder_name)s doesn't exists for account %(account_login)s."
                )
                % (
                    {
                        "folder_name": webmail_folder.technical_name,
                        "account_login": webmail_folder.webmail_account_id.login,
                    }
                )
            ) from e

        # TODO ADD : [u'SINCE', date(2005, 4, 3)]
        message_ids = client.search(["NOT", "DELETED"])
        mail_datas = client.fetch(
            message_ids, ["INTERNALDATE", "FLAGS", "RFC822.SIZE", "ENVELOPE"]
        )

        for _message_id, mail_data in mail_datas.items():
            self._get_or_create(webmail_folder, mail_data)

        client.logout()

    def _get_or_create(self, webmail_folder, mail_data):
        envelope = mail_data[b"ENVELOPE"]
        identifier = envelope.message_id.decode()
        reply_identifier = (
            envelope.in_reply_to and envelope.in_reply_to.decode() or False
        )
        vals = {
            "folder_id": webmail_folder.id,
        }

        # Check if mail exists in Odoo
        existing_mail = self.search(
            [
                ("identifier", "=", identifier),
            ]
        )
        if existing_mail:
            if existing_mail.folder_id != webmail_folder:
                existing_mail.write(vals)
            return existing_mail

        origin_mail = self.search(
            [
                ("identifier", "=", reply_identifier),
            ]
        )

        other_mails = self.search(
            [
                ("reply_identifier", "=", identifier),
            ]
        )

        vals.update(
            {
                "identifier": identifier,
                "date_mail": envelope.date,
                "reply_identifier": reply_identifier,
                "origin_mail_id": origin_mail and origin_mail.id,
                "subject": envelope.subject,
                "sender": self._get_mail_from_address(envelope.sender[0]),
                "envelope_data": str(envelope),
            }
        )

        _logger.info(
            "fetch from the upstream mail server."
            " Account %s. Creation of mail %s"
            % (webmail_folder.webmail_account_id.name, identifier)
        )
        new_mail = self.create(vals)

        if other_mails:
            other_mails.write(
                {
                    "origin_mail_id": new_mail.id,
                }
            )

        return new_mail
        # import pdb; pdb.set_trace()
        # print('{id}: {size} bytes, flags={flags}, {subject}'.format(
        #     id=message_id,
        #     subject=data[b'ENVELOPE'].subject.decode(),
        #     size=data[b'RFC822.SIZE'],
        #     flags=data[b'FLAGS']))

    def _get_mail_from_address(self, address):
        return "%s@%s" % (address.mailbox.decode(), address.host.decode())
