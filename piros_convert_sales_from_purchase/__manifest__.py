# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name' : "Convert Sales from Purchase Order",
    'version' : "11.0.0.1",
    'author' : "BrowseInfo",
    'summary': 'This apps helps to Covert Sale order from Purchase Order',
    'description' : """
        Convert Sale from purchase Order
        Convert Sales from purchase Order
        Convert Sales order from purchase Order
        Convert Sale order from purchase Order

        create Sale from purchase Order
        create Sales from purchase Order
        create Sales order from purchase Order
        create Sale order from purchase Order

        create Sale from purchase Order
        create Sales from purchase Order
        create Sales order from purchase Order
        create Sale order from purchase Order

     """,
    'category' : "Sales",
    'website'  : "https://www.browseinfo.in",
    'depends' : [ 'base', 'product','sale_management','purchase','piros'],    
    'data' : [
            'wizard/sale_order_wizard_view.xml',
            'views/main_purchase_order_view.xml',
            ],

    'test' :  [ ],
    'css'  :  [ ],
    'demo' :  [ ],
    'installable' : True,
    'application' :  False,
    "images":['static/description/Banner.png'],
}
