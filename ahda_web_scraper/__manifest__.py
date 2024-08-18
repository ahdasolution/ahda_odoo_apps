{
    "name": "Web Scraper for Odoo",
    "author": "AHDA Tech Solution",
    "category": "Uncategorized",
    "version": "13.0.0",
    "license" : "LGPL-3",
    "depends": ["base", "mail"],
    "summary": """
This module allows you to scrape a website and do something in odoo with the data""",
    "data": [
        "security/ir.model.access.csv",
        "views/scraper.xml",
        "views/menu_items.xml",
    ],
    "application": True,
}
