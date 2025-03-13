# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import email
import logging
import hashlib

import chardet
from bs4 import BeautifulSoup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"
    _order = "date_mail desc"

    date_mail = fields.Datetime(required=True, readonly=True)

    folder_id = fields.Many2one(
        comodel_name="webmail.folder",
        ondelete="cascade",
        required=True,
        readonly=True,
    )

    identifier = fields.Char(required=True, readonly=True)

    origin_mail_id = fields.Many2one(comodel_name="webmail.mail", readonly=True)

    reply_identifier = fields.Char(readonly=True)

    subject = fields.Char(readonly=True)

    sender = fields.Char(readonly=True)

    user_id = fields.Many2one(
        comodel_name="res.users",
        related="folder_id.user_id",
        store=True,
        readonly=True,
    )

    body_plain = fields.Text(readonly=True)

    def _fetch_mails(self, webmail_folder):
        _logger.info(f"Fetching Mails for folder {webmail_folder.technical_name}")
        client = webmail_folder.webmail_account_id._get_client_connected()
        status, select_code = client.select(f'"{webmail_folder.technical_name}"')
        if status != "OK":
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
            )
        status, search_result = client.search(None, "ALL")
        num_list = search_result[0].split()
        for num in num_list:
            _logger.info(
                f" {num.decode()}/{len(num_list)}: Get Mail in {webmail_folder.technical_name})."
            )
            status, mail_data = client.fetch(num, "(RFC822)")
            self._create_or_update_mail(webmail_folder, mail_data)
        client.logout()

    def _create_or_update_mail(self, webmail_folder, mail_data):
        email_message = email.message_from_bytes(
            mail_data[0][1], policy=email.policy.default
        )
        identifier = self._get_identifier_from_message(email_message, mail_data[0][1])
        reply_identifier = email_message["In-Reply-To"]
        vals = {"folder_id": webmail_folder.id}

        # Check if mail exists in Odoo
        existing_mail = self.search([("identifier", "=", identifier)])
        if existing_mail:
            if existing_mail.folder_id != webmail_folder:
                existing_mail.write(vals)
            return existing_mail

        origin_mail = self.search([("identifier", "=", reply_identifier)])
        other_mails = self.search([("reply_identifier", "=", identifier)])

        vals.update(
            {
                "identifier": identifier,
                "date_mail": self._get_date_from_message(email_message),
                "reply_identifier": reply_identifier,
                "origin_mail_id": origin_mail and origin_mail.id,
                "subject": self._get_subject_from_message(email_message),
                "sender": email_message["From"],
                "body_plain": self._get_body_plain_from_message(email_message),
            }
        )

        _logger.debug(
            f" Fetch Mail {identifier}. (Account {webmail_folder.webmail_account_id.name})"
        )
        try:
            new_mail = self.create(vals)
        except:
            import pdb; pdb.set_trace()
        if not other_mails:
            return
        other_mails.write({"origin_mail_id": new_mail.id})

    @api.model
    def _get_identifier_from_message(self, email_message, message_bytes):
        identifier = email_message["Message-ID"]
        if not identifier:
            identifier = hashlib.sha256(message_bytes).hexdigest()
        return identifier

    @api.model
    def _get_subject_from_message(self, email_message):
        if not email_message["Subject"]:
            return ""
        parts = email.header.decode_header(email_message["Subject"])
        result = []
        for part in parts:
            if isinstance(part[0], bytes):
                if part[1]:
                    result.append(part[0].decode(part[1]))
                else:
                    result.append(part[0].decode())
            else:
                result.append(part[0])
        return "".join(result).replace("\x00" ,"")

    @api.model
    def _get_date_from_message(self, email_message):
        if "Date" in email_message:
            # TODO, FIXME, handle timezone
            date = email.utils.parsedate_to_datetime(email_message["Date"])
        elif "Received" in email_message:
            date = email.utils.parsedate_to_datetime(
                email_message["Received"].split(";")[-1]
            )
        else:
            import pdb

            pdb.set_trace()
        return date.replace(tzinfo=None)

    @api.model
    def _get_body_plain_from_message(self, email_message):
        body_plain = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))
                # skip any text/plain (txt) attachments
                if ctype == "text/plain" and "attachment" not in cdispo:
                    body_plain = part.get_payload(decode=True)
                    break
                if ctype == "text/html":
                    html = part.get_payload(decode=True)
                    soup = BeautifulSoup(html, features="lxml")
                    body_plain = soup.get_text()
                    break
        else:
            body_plain = email_message.get_payload(decode=True)

        if body_plain:
            try:
                return body_plain.decode()
            except:
                try:
                    if type(body_plain) is str:
                        return body_plain
                    detection = chardet.detect(body_plain)
                    return body_plain.decode(detection.get("encoding"))
                except:
                    print("=================================================")
                    print(body_plain)
                    print("=================================================")
                    import pdb

                    pdb.set_trace()
        return ""
