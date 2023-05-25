# Copyright (C) 2023 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Webmail",
    "summary": "Odoo as a Webmail",
    "version": "16.0.1.0.0",
    "category": "R&D",
    "author": "GRAP",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/legalsylvain/webmail",
    "license": "AGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    "external_dependencies": {"python": ["imapclient"]},
    "data": [
        "security/ir_module_category.xml",
        "security/ir_rule.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/view_webmail_account.xml",
    ],
    "demo": [
        # "demo/res_groups.xml",
        # "demo/pos_config.xml",
        # "demo/pos_place.xml",
    ],
}
