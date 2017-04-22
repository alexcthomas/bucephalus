
var buildTagString = function(tags){
	var ret = [];
	
	$.each(tags, function(i, item) {
		ret.push({"name":"tags",  "value":i+":"+item});
	});
	
	return ret;
}

var renderView = function(target, info, tags) {
	var alltags = Object.assign({}, tags, info.tags);
	var rendererName = info.renderer;
	var extra = buildTagString(alltags);
	var params = [{"name":"type", "value":info.viewtype}].concat(extra);
	var url = "/view?" + $.param(params);
	
	$.getJSON(url, function(d) {
		ViewRenderers.render(rendererName, target, d);
	});
};

// figures out the content pane layout
// and hands off the view rendering to renderView
var renderContentPane = function(views, tags) {
	
	var navData = $("#sidebar-nav").data("viewdata");
	var viewdata, pagetags;
	
	if (views == undefined) {
		viewdata = navData['Root'].views;
		pagetags = navData['Root'].tags
	} else {
		viewdata = views
		pagetags = tags
	}
	
	var tgt = $("#page-content");
	tgt.html('');
	
	var rows = {};
	
	$.each(viewdata, function(i, item) {
		var viewTarget = $('<div/>');
		if (rows[item.row]==undefined){
			viewTarget.addClass("view_row_start");
			rows[item.row] = [];
		} else {
			viewTarget.addClass("view_row_cont");
		}
		rows[item.row].push(viewTarget);
		viewTarget.data("viewdata", item);
		tgt.append(viewTarget);
		renderView(viewTarget, item, pagetags) // could add an optional div size here
	});
	tgt.data("rows", rows);
};
