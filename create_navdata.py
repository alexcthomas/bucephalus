import ujson

navdata = [{
        'title': 'Root',
        'display': False,
        'tags': {},
        'views': [{
            'row': 1,
            'viewtype': 'overview_bar',
            'renderer': 'highcharts'
        }, {
            'row': 2,
            'viewtype': 'overview_distribution',
            'renderer': 'img'
        }]
    }, {
        'title': 'Option1',
        'tags': {
            'tag1': 'value11',
            'tag2': 'value21'
        },
        'views': [{
            'row': 1,
            'viewtype': 'prices',
            'renderer': 'highcharts'
        }, {
            'row': 1,
            'viewtype': 'volatilities',
            'renderer': 'highcharts'
        }, {
            'row': 2,
            'viewtype': 'explanation',
            'renderer': 'html'
        }, {
            'row': 2,
            'viewtype': 'curve',
            'renderer': 'highcharts'
        }]
    }, {
        'title': 'Option2',
        'tags': {
            'tag1': 'value12',
            'tag2': 'value22'
        },
        'views': [{
            'row': 1,
            'viewtype': 'parabola',
            'renderer': 'img'
        }]
    }

]

with open(r'static\json\navdata.json', 'w') as fh:
    ujson.dump(navdata, fh)

