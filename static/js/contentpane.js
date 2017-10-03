
// builds the url for getting data
var buildTagString = function(tags){
	var ret = [];
	
	$.each(tags, function(i, item) {
		ret.push({"name": "tags", "value": i+":"+item});
	});
	
	return ret;
}

var isDataEmpty = function(data) {
	var result = true
	$.each(data, function (i, obj) {
		$.each(obj.data, function (index, arr) {
			if (arr[1] != 0) {
				result = false;
			};
        });
    });
	return result;
};

var renderView = function(target, info, definition, seriesNameToData) {
	var data = [];
	$.each(definition.series, function(i, series) {
		data.push({name: series, data: seriesNameToData[series]});
	});
	definition.series = data;

	if (isDataEmpty(data)) {
		console.log('Data is empty:', data[0].name);
		target.css('display', 'none');
    } else {
        ViewRenderers.render(definition.renderer, target, definition);
    }
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
var renderContentPane = function(views, tags, title) 
{
	// Create the views up front, then query for their data and initialise them as it arrives
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
	var viewContainers = createViews(rows, pagetags);

	// Set the page title
	if (pagetitle == undefined){
		pagetitle = "Bucephalus Dashboard";
	}
	$('#page-header-title').text(pagetitle);

	progressBar.progressbar('value', false);
	loadingDialog.dialog('open');
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
		url: '/views',
		complete: function() {
			loadingDialog.dialog('close');
		},
		xhrFields: {
			onprogress: function(e) {
				// We cannot make assumptions about where the data is chunked in transport so we look
				// for the separator semicolons. 
				var current, response = e.currentTarget.response;
				var nextSemicolonIdx;

				while (-1 != (nextSemicolonIdx = response.indexOf(';', lastProcessedIdx))) {
					// Extract a chunk from the data received so far
					var chunk = response.substring(lastProcessedIdx, nextSemicolonIdx);
					//console.log(Date.now() + ': chunk ' + lastProcessedIdx + '..' + nextSemicolonIdx);
					var chunkObj = JSON.parse(chunk);
					lastProcessedIdx = nextSemicolonIdx+1;

					// Process the chunk - generate the view
					if (chunkObj.category == 'data') {
						//console.log('Data [' + chunkObj.series + ']');
						dataBlocks[chunkObj.series] = chunkObj.data;
					} else if (chunkObj.category == 'graph') {
                        var reference_id = chunkObj.id;
                        //console.log('GRAPH ' + reference_id);
                        var definition = viewContainers[reference_id];
                        renderView(definition.target, definition.view, chunkObj.result, dataBlocks);
                    } else if (chunkObj.category == 'status') {
						progressBar.progressbar('option', 'max', chunkObj.maxIndex);
						progressBar.progressbar('value', chunkObj.index);
					} else {
						console.log('Unknown category "' + chunkObj.category + '"');
					}
				} 
			}	
		},
		data: JSON.stringify(rows),
		contentType: 'application/json; charset=utf-8',
		dataType: 'json'
	});
};

var createViews = function(rows, pagetags) {
	var tgt = $("#page-content");
	tgt.html('');
	
	var width = tgt.width();
	var views = [];

	$.each(rows, function(i, row) {
		var nviews = row.length;
		if (nviews!=0) {
			var viewWidth =  (width / nviews) - 20; // margin of the views div

			$.each(row, function(j, view) {
				var viewTarget = createPanel(viewWidth);
				if (j==0){
					viewTarget.addClass("view_row_start");
				} else {
					viewTarget.addClass("view_row_cont");
				}
				tgt.append(viewTarget);
				views.push({'target': viewTarget, 'view': view});
			});
		}
	});

	return views;
};



