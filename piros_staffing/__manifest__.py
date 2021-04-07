{
        'name':'Piros Staffing',
        'summary':"""This module will add the posibility to log Piros proposed profiles""",
        'version':'0.1',
        'description':"""This module will add the posibility to log Piros proposed profiles""",
        'author':'Martijn Cielen',
        'company':'Piros',
        'website':'https://piros.be',
        'category':'Tools',
        'depends':['base'],
        'license':'AGPL-3',
        'data': [
            'views/view.xml',
            'security/ir.model.access.csv'
        ],
        'demo':[],
        'installable': True,
        'auto_install': False,
        'depends': ['base', 'hr'],
}

