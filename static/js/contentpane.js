
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
	var renderer = ViewRenderers.getRenderer(rendererName, target);
	var extra = buildTagString(alltags);
	var params = [{"name":"type","value":info.viewtype}].concat(extra);
	var url = "/view?" + $.param(params);
	
	$.getJSON(url, renderer);
};

// figures out the content pane layout
// and hands off the view rendering to renderView
var renderContentPane = function(pageName) {
	
	if (pageName == undefined) {
		var title = 'Parent1';
	} else {
		var title = pageName;
	}
	
	var navData = $("#sidebar-nav").data("viewdata");
	var data = navData[title].views;
	var tgt = $("#page-content");
	tgt.html('');
	var pagetags = navData[title].tags
	
	var rows = {};
	
	$.each(data, function(i, item) {
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
