# Copyright (C) 2023 - Today: OaaFS
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Webmail",
    "summary": "Odoo as a Webmail",
    "version": "16.0.1.0.0",
    "category": "R&D",
    "author": "OaaFS",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/mis-builder",
    "license": "AGPL-3",
    "depends": [
        "base",
        # OCA
        "queue_job",
    ],
    "external_dependencies": {"python": ["imapclient"]},
    "data": [
        "security/ir_module_category.xml",
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/view_webmail_host.xml",
        "views/view_webmail_account.xml",
        "views/view_webmail_folder.xml",
        "views/view_webmail_mail.xml",
    ],
    "demo": [
        "demo/webmail_host.xml",
    ],
}
