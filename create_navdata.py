import json

navdata = [{
        'title': 'Option1',
        'tags': {
            'tag1': 'value11',
            'tag2': 'value21'
        },
        'views': [{
            'pane': 'pane1',
            'url': '/views?name=view1&tag1=value11&tag2=value21'
        }]
    }, {
        'title': 'Option2',
        'tags': {
            'tag1': 'value12',
            'tag2': 'value22'
        },
        'views': [{
            'pane': 'pane1',
            'url': '/views?name=view1&tag1=value12&tag2=value22'
        }]
    }

]

with open(r'static\json\navdata.json', 'w') as fh:
    json.dump(navdata, fh)

