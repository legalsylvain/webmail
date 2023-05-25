# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import socket
import imapclient
import imaplib

from odoo import _, fields, models
from odoo.exceptions import UserError

class WebmailHost(models.Model):
    _name = "webmail.host"
    _description = "Webmail Hosts"

    name = fields.Char(required=True)

    url = fields.Char(required=True)
