
// builds the url for getting data
var buildTagString = function(tags){
	var ret = [];
	
	$.each(tags, function(i, item) {
		ret.push({"name": "tags", "value": i+":"+item});
	});
	
	return ret;
}

var renderView = function(target, info, definition, seriesNameToData) {
	var data = [];

	$.each(definition.series, function(i, series) {
		data.push({name: series[1], data: seriesNameToData[series]});
	});

	definition.series = data;
	ViewRenderers.render(info.renderer, target, definition);

};

var createPanel = function(width, height) {
	var inner = $('<div/>')
		.addClass("panel-body");
	var ret = $('<div/>')
		.addClass("panel panel-default")
		.css('width', width.toString()+'px')
		.css('height', height.toString()+'px')
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

var getErrorTarget = function(viewdata, viewinfo) {

	// if this error is relevant to a particular view, then get the target
	if ('id' in viewdata) {
		return viewinfo.targets[viewdata.id];
	}

	// else it's a page error, so reset the target divs
	var tgt = $("#page-content");
	tgt.html('');
	var width = tgt.width();
	var viewTarget = createPanel(width - 10);
	viewTarget.addClass("view_row_start");
	tgt.append(viewTarget);
	return viewTarget;

}

var parseChunk = function(chunk, dataBlocks, viewinfo) {

	var chunkObj = JSON.parse(chunk);

	// Process the chunk - generate the view
	if (chunkObj.category == 'data') {
		dataBlocks[chunkObj.series] = chunkObj.data;
	} else if (chunkObj.category == 'graph') {
		var target = viewinfo.targets[chunkObj.id];
		var viewdef = viewinfo.definitions[chunkObj.id];
		renderView(target, viewdef, chunkObj.result, dataBlocks);
	} else if (chunkObj.category == 'error') {
		var target = getErrorTarget(chunkObj, viewinfo);
		ViewRenderers.render('error', target, chunkObj.message);
	}
}

// figures out the content pane layout
// and hands off the view rendering to renderView
var renderContentPane = function(views, tags, title) 
{
	// Create the views up front, then query for their data and initialise them as it arrives
	var token = $("#sidebar-token-form :selected").text();
	var navData = $("#sidebar-nav").data("viewdata");
	var viewdata, pagetags, pagetitle;
	
	if (views == undefined) {
		viewdata = navData['Root'].views;
		pagetags = navData['Root'].tags;
		pagetitle = navData['Root'].title;
	} else {
		viewdata = views;
		pagetags = tags;
		pagetitle = title;
	}

	var rows = getViewRows(viewdata);
	var viewinfo = createViewDivs(rows, pagetags);

	// Set the page title
	if (pagetitle == undefined){
		pagetitle = "Bucephalus Dashboard";
	}
	$('#page-header-title').text(pagetitle);

	// Send the JSON for this page to the server in one block so we can do all the queries in one go.
	// We expect to receive back a series of blocks.  Each block will be either a graph block or
	// a named data block - seems complicated, but means we can combine data (i.e. if graph A and B both
	// require a data source S then we only send S once.)
	// Guarantees/warnings:
	// 1. We will not encounter any graph block until we have received the data it depends on
	// 2. Graph blocks will be received in order specified
	// 3. Note that server-side graphs (e.g. matplotlib) would not have associated data blocks
	var lastProcessedIdx = 0;
	var dataBlocks = {};

	$.ajax({
		type: 'POST',
		url: '/views/'+token,
		xhrFields: {
			onprogress: function(e) {
				var nextSemicolonIdx, response = e.currentTarget.response;

				while (-1 != (nextSemicolonIdx = response.indexOf(';', lastProcessedIdx))) {
					var chunk = response.substring(lastProcessedIdx, nextSemicolonIdx);
					lastProcessedIdx = nextSemicolonIdx+1;
					parseChunk(chunk, dataBlocks, viewinfo);
				} 
			}	
		},	
		complete: function(a,b,c) {
			// IE11 calls the 'complete' callback when the response is complete, rather than onprogress
			var nextSemicolonIdx, response = a.responseText;

			while (-1 != (nextSemicolonIdx = response.indexOf(';', lastProcessedIdx))) {
				var chunk = response.substring(lastProcessedIdx, nextSemicolonIdx);
				lastProcessedIdx = nextSemicolonIdx+1;
				parseChunk(chunk, dataBlocks, viewinfo);
			} 
		},
		data: JSON.stringify(viewinfo.definitions),
		contentType: 'application/json; charset=utf-8',
		dataType: 'json',
		cache: false,
		timeout: 0,
		json: true
	});
};

// https://stackoverflow.com/questions/288699/get-the-position-of-a-div-span-tag
function getPos(el) {
    // yay readability
    for (var lx=0, ly=0;
         el != undefined;
         lx += el.offsetLeft, ly += el.offsetTop, el = el.offsetParent);
    return {x: lx,y: ly};
}

var createViewDivs = function(rows, pagetags) {
	var tgt = $("#page-content");
	tgt.html('');
	
	var viewHeight = 450;
	var width = tgt.width();
	var availableHeight = $(window).height() - getPos(tgt[0]).y - 5; // Subtract the header height and bottom padding
	var nRows = rows.length;
	var totalViewHeight = nRows * (viewHeight + 10); // (View height plus margin) times # rows

	if (totalViewHeight >= availableHeight) {
		width = width - 300; // Scroll bar will appear, so remove its width
	}

	var viewTargets = [];
	var viewsDefs = [];

	$.each(rows, function(i, row) {
		var nviews = row.length;
		if (nviews!=0) {
			var viewWidth = (width / nviews) - 10; // margin of the views div

			$.each(row, function(j, view) {
				var viewTarget = createPanel(viewWidth, viewHeight);
				if (j==0){
					viewTarget.addClass("view_row_start");
				} else {
					viewTarget.addClass("view_row_cont");
				}
				tgt.append(viewTarget);
				viewTargets.push(viewTarget);
				viewsDefs.push(view);
			});
		}
	});

	return {'targets': viewTargets, 'definitions': viewsDefs};
};



