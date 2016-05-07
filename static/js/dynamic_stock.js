$(function () {
    $(document).ready(function () {
        Highcharts.setOptions({
            global: {
                useUTC: false
            }
        });
        $('#container2').highcharts('StockChart', {
            chart: {
                events: {
                    load: function () {
                        var series = this.series[0];
                        setInterval(function () {
                            var t = (new Date()).getTime();
                            $.getJSON($SCRIPT_ROOT + '/rand', {
                                t: t
                            }, function(data){
                                var x = t, y = data.result;
                            series.addPoint([x, y], true, true);
                            })
                        }, 1000);
                    }
                }
            },
            rangeSelector: {
                buttons: [{
                    count: 1,
                    type: 'minute',
                    text: '1M'
                }, {
                    count: 5,
                    type: 'minute',
                    text: '5M'
                }, {
                    type: 'all',
                    text: 'All'
                }],
                inputEnabled: false,
                selected: 0
            },
            title : {
                text : 'Live random data'
            },
            exporting: {
                enabled: false
            },

            series : [{
                name : 'Random data',
                // initialization of data
                data : (function () {
                    var data = [], time = (new Date()).getTime(), i;
                    for (i = -999; i <= 0; i += 1) {
                        data.push([
                            time + i * 1000,
                            0 
                        ]);
                    }
                    return data;
                }())
            }]
        });
    });
});
