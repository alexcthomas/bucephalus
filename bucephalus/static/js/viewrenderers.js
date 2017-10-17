
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
		target.html(data.result);
	},

	tableRenderer: function(target, data) {
		// not implemented
	},

	errorRenderer: function(target, data) {
		$('<pre/>').html(data)
			.appendTo(target);
	},

	render: function(rendererName, target, data) {
		this.renderers[rendererName](target, data);
	}
};

// http://stackoverflow.com/a/6844046
ViewRenderers.renderers = {
	highcharts: ViewRenderers.highchartsRenderer,
	highstock: ViewRenderers.highstockRenderer,
	img: ViewRenderers.imgRenderer,
	html: ViewRenderers.htmlRenderer,
	table: ViewRenderers.tableRenderer,
	error: ViewRenderers.errorRenderer
};

