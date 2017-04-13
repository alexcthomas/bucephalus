var ViewRenderers = {
	
	highchartsRenderer: function(target, data) {
		target.highcharts(data);
	},
	
	highstockRenderer: function(target, data) {
		Highcharts.stockChart(target[0], data);
	},

	imgRenderer: function(target, data) {
		$('<img/>', {src: data.result})
			.appendTo(target);
	},

	htmlRenderer: function(target, data) {
		var a=1;
	},

	tableRenderer: function(target, data) {
		var a=1;
	},
	
	getRenderer: function(rendererName, target){
		var renderer = this.renderers[rendererName];
		return (function(data) {
			renderer(target, data);
		});
	}
};

// http://stackoverflow.com/a/6844046
ViewRenderers.renderers = {
	highcharts: ViewRenderers.highchartsRenderer,
	highstock: ViewRenderers.highstockRenderer,
	img: ViewRenderers.imgRenderer,
	html: ViewRenderers.htmlRenderer,
	table: ViewRenderers.tableRenderer
};

