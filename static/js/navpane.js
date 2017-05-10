
// Returns the location of a node for encoding in a url
var getNodeLocation = function(node) {
	var tree = $("#sidebar-nav").data("treeview");

	var cnt = 1;
	var loc = [];
	var ret = [];

	do {
		loc.push(node.text);
		node = tree.getParent(node);
	}
	while (node != undefined)

	loc = loc.reverse();

	for (var i = 0; i < loc.length; i++) {
		ret.push({"name": "level"+cnt.toString(), "value": loc[i]});
		cnt = cnt + 1;
	}

	return ret;
}

// Gets a node location from the url
function getJsonFromUrl() {
	var query = location.search.substr(1);
	var result = [];
	if (query.length==0){
		return result
	}
	query.split("&").forEach(function(part) {
		var item = part.split("=");
		result.push(decodeURIComponent(item[1]));
	});
	return result;
}

// checks whether a node matches a location given in a url
var parentMatch = function(tree, node, levels) {
	if (levels.length==0){
		return true;
	}
	if (node.text!=levels.slice(-1)) {
		return false;
	} else {
		return parentMatch(tree, tree.getNode(node.parentId), levels.slice(0,-1));
	}
}

// selects the node that matches the location given in a url
var selectNode = function(tgt, levels) {

	if (levels.length==0){
		renderContentPane();
	} else {
		var tree = tgt.data("treeview");
		var nodeName = levels.slice(-1);
		var nodes = tree.getNodes(nodeName, "g");

		for (var i = 0; i < nodes.length; i++) {
			var node = nodes[i];
			if (parentMatch(tree, node, levels)) {
				tree.selectNode(node);
				if (node.parentId!=undefined) {
					tree.expandNode(node.parentId);
				}
			}
		}
	}
};

// gets called when a tree node is selected
var treeNodeSelect = function(event, node) {
	renderContentPane(node.views, node.tags);

	var nodeLocation = getNodeLocation(node);
	var nodeUrl = "?" + $.param(nodeLocation);
	window.history.pushState("", "", nodeUrl);
};

// gets called when a tree node is unselected
var treeNodeUnSelect = function(event, node) {
	$("#page-content").html('');
	
	// If this node has been manually deselected, rather than
	// another node being selected, then render the root page
	if (node.unselected){
		renderContentPane();
		window.history.pushState("", "", "/");
	}
};

var renderSimulationSelectorCallback = function(event) {
	console.log(event.data.token);
	$("#simulation-dropdown-btn").dropdown("toggle");
    $('#simulation-dropdown-items').css({
		position: '',
		display: 'none',
		left: '',
		top: ''
	});
    $.getJSON('/set_token?token=' + event.data.token);
};

var renderSimulationSelector = function() {
	var list = document.getElementById("simulation-dropdown-items");
	$.getJSON('/get_tokens', function(items) {
        $.each(items, function (i, v) {
            var li = document.createElement("li");
            var link = document.createElement("a");
            var text = document.createTextNode(v);
            list.appendChild(li);
            link.href = "javascript:void(0);";
			$(link).click({token: v}, renderSimulationSelectorCallback);
            li.appendChild(link);
            link.appendChild(text);
        })
    });

	// Fix to allow the pop-up menu to float over the top of the surrounding elements
    $('#simulation-dropdown-btn').click(function(e) {
        $('#simulation-dropdown-items').css({
            position: 'fixed',
            display: 'block',
            left: e.pageX,
            top: e.pageY
        })
    });
};

// gets data to fill out the nav pane
var renderNavPane = function() {
	$.getJSON("/navdata",
	function(data) {
		var tgt = $("#sidebar-nav");
		var viewdata = {};
		var currentUrl = getJsonFromUrl();
		
		$.each(data, function(key, val) {
			viewdata[val.text] = val;
		});
		
		// if there's a root page, remove it so it doesn't get put into the tree
		if (data[0].text == "Root"){
			data.splice(0,1)
		}
		
		// build the nav tree
		var tree = tgt.treeview({
			levels: 1,
			data: data,
			onNodeSelected: treeNodeSelect,
			onNodeUnselected: treeNodeUnSelect
		});
		
		//bind the data to the div element just in case
		tgt.data("viewdata", viewdata);

		//select the node given by the url
		selectNode(tgt, currentUrl);
	});
};









