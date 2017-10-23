
function changeToken(form, event) {
	var token = $("#sidebar-token-form :selected").text();
	renderNavPane(token);
}

function showTokens() {
	var target = $("#sidebar-token-picker");
	$.getJSON('/get_tokens',
		function(items) {
			$.each(items, function (i, item) {
				target.append($('<option>', {value: item, text : item}))
			});
			// if (token != undefined) {
			// 	target.selectpicker('val', token);
			// }
			target.selectpicker('refresh');
			changeToken();
		}
	);
}

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
	while (node != undefined);

	loc = loc.reverse();

	for (var i = 0; i < loc.length; i++) {
		ret.push({"name": "level"+cnt.toString(), "value": loc[i]});
		cnt = cnt + 1;
	}

	return ret;
};

// Gets a node location from the url
function getJsonFromUrl() {
	var query = location.search.substr(1);
	var result = [];
	if (query.length==0){
		return result;
	}
	query.split("&").forEach(function(part) {
		var item = part.split("=");
		result.push(decodeURIComponent(item[1]));
	});
	return result;
}

// checks whether a node matches a location given in a url
var parentMatch = function(tree, node, levels) {
	if (levels.length==0) {
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
	renderContentPane(node.views, node.tags, node.title);

	var nodeLocation = getNodeLocation(node);
	var nodeUrl = "?" + $.param(nodeLocation);
	window.history.pushState("", "", nodeUrl);
};

// gets called when a tree node is unselected
var treeNodeUnSelect = function(event, node) {
	$("#page-content").html('');
	
	// If this node has been manually deselected, rather than
	// another node being selected, then render the root page
	if (node.unselected) {
		renderContentPane();
		window.history.pushState("", "", "/");
	}
};

// gets data to fill out the nav pane
var renderNavPane = function(token) {
	$.getJSON("/navdata/"+token,
	function(data) {
		var tgt = $("#sidebar-nav");
		tgt.html("");
		var viewdata = {};
		var currentUrl = getJsonFromUrl();

		$.each(data, function(key, val) {
			viewdata[val.text] = val;
		});

		// if there's a root page, remove it so it doesn't get put into the tree
		if (data[0].text == "Root") {
			data.splice(0,1);
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