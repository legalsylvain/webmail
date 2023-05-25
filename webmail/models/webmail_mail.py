# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WebmailMail(models.Model):
    _name = "webmail.mail"
    _description = "Webmail Mail"

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

    # client.select_folder('INBOX')

    # # search criteria are passed in a straightforward way
    # # (nesting is supported)
    # messages = client.search(['NOT', 'DELETED'])

    # # fetch selectors are passed as a simple list of strings.
    # response = client.fetch(messages, ['FLAGS', 'RFC822.SIZE', 'ENVELOPE'])

    # # `response` is keyed by message id and contains parsed,
    # # converted response items.
    # for message_id, data in response.items():
    #     import pdb; pdb.set_trace()
    #     print('{id}: {size} bytes, flags={flags}, {subject}'.format(
    #         id=message_id,
    #         subject=data[b'ENVELOPE'].subject.decode(),
    #         size=data[b'RFC822.SIZE'],
    #         flags=data[b'FLAGS']))