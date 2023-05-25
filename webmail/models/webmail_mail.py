# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import fields, models
_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        required=True,
        readonly=True,
    )

    identifier = fields.Char(required=True)

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    def _fetch_mails(self, webmail_folder):
        client = webmail_folder.webmail_account_id._get_client_connected()
        try:
            client.select_folder(webmail_folder.technical_name)
        except imaplib.IMAP4.error as e:
            client.logout()
            raise UserError("Folder %s doesn't exists for account %s." % (webmail_folder.technical_name, webmail_folder.webmail_account_id.login))  from e

        # TODO ADD : [u'SINCE', date(2005, 4, 3)]
        message_ids = client.search(['NOT', 'DELETED'])
        response = client.fetch(message_ids, ["INTERNALDATE", 'FLAGS', 'RFC822.SIZE', 'ENVELOPE'])

        for message_id, mail_data in response.items():
            self._get_or_create(webmail_folder, mail_data)

    def _get_or_create(self, webmail_folder, mail_data):
        vals = {
            "identifier":  mail_data[b"ENVELOPE"].message_id.decode(),
            "folder_id": webmail_folder.id,
        }

        # Check if mail exists in Odoo
        existing_mail = self.search(
            [
                ("identifier", "=", vals["identifier"]),
            ]
        )
        if existing_mail:
            # TODO, maybe update data ?
            return existing_mail

        vals.update({})

        _logger.info(
            "fetch from the upstream mail server."
            " Account %s. Creation of mail %s"
            % (webmail_folder.webmail_account_id.name, vals["identifier"])
        )
        return self.create(vals)


            # import pdb; pdb.set_trace()
            # print('{id}: {size} bytes, flags={flags}, {subject}'.format(
            #     id=message_id,
            #     subject=data[b'ENVELOPE'].subject.decode(),
            #     size=data[b'RFC822.SIZE'],
            #     flags=data[b'FLAGS']))