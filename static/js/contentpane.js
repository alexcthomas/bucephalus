
// builds the url for getting data
var buildTagString = function(tags){
	var ret = [];
	
	$.each(tags, function(i, item) {
		ret.push({"name": "tags", "value": i+":"+item});
	});
	
	return ret;
}

var renderView = function(target, info, tags, seriesNameToData) {
	var alltags = Object.assign({}, tags, info.tags);
// 	var rendererName = info.renderer;
// 	var extra = buildTagString(alltags);
// 	var params = [{"name":"type", "value":info.viewtype}].concat(extra);
// 	var url = "/view?" + $.param(params);
	
// 	$.getJSON(url, function(d) {
// 		ViewRenderers.render(rendererName, target, d);
// 	});
	var data = seriesNameToData[alltags['series']]; 
	ViewRenderers.render(info.renderer, target, data);
};

var createPanel = function(width) {
	var inner = $('<div/>')
		.addClass("panel-body");
	var ret = $('<div/>')
		.addClass("panel panel-default")
		.css('width', width.toString()+'px')
		.append(inner);
	return ret;
}

var getViewRows = function(viewdata) {

	var rows = [];

	$.each(viewdata, function(i, item) {
		if (rows[item.row-1]==undefined) {
			rows.push([item]);
		} else {
			rows[item.row-1].push(item);
		}
	});

	return rows;
}

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

	var rows = getViewRows(viewdata);
	
	// Send the JSON to the server in one block so we can do all the queries in one go
	$.ajax({type: 'POST',
		url: '/views',
		data: JSON.stringify(rows),
		contentType: 'application/json; charset=utf-8',
		dataType: 'json',
		success: function(response) {
			var seriesNameToData = {};
			for(i = 0; i < response.length; i++) {
				key = Object.keys(response[i])[0];
				seriesNameToData[key] = Object.values(response[i])[0];
			}
			createViews(seriesNameToData, rows, pagetags);
		}
	});
};

var createViews = function(seriesNameToData,rows, pagetags) {
	var tgt = $("#page-content");
	tgt.html('');
	
	var width = tgt.width();
	
	$.each(rows, function(i, row) {
		var nviews = row.length;
		if (nviews!=0) {
			var viewWidth =  (width / nviews) - 10 // margin of the views div

			$.each(row, function(j, view) {
				var viewTarget = createPanel(viewWidth);
				if (j==0){
					viewTarget.addClass("view_row_start");
				} else {
					viewTarget.addClass("view_row_cont");
				}
				tgt.append(viewTarget);
				renderView(viewTarget, view, pagetags, seriesNameToData);
			});
		}
	});
}



