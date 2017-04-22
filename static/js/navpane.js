
var treeNodeSelect = function(event, node) {
	renderContentPane(node.views, node.tags);
}

var treeNodeUnSelect = function(event, node) {
	$("#page-content").html('');
	
	// If this node has been manually deselected, rather than
	// another node being selected then render the root page
	if (node.unselected){
		renderContentPane();
	}
}

// gets data to fill out the nav pane
var renderNavPane = function(callafter) {
	$.getJSON("/navdata", 
	function(data) {
		var tgt = $("#sidebar-nav");
		var viewdata = {};
		
		$.each(data, function(key, val) {
			viewdata[val.text] = val;
		});
		
		// if there's a root page, remove it so it doesn't get put into the tree
		if (data[0].text == "Root"){
			data.splice(0,1)
		}
		
		var tree = tgt.treeview({
			levels: 1,
			data: data,
			onNodeSelected: treeNodeSelect,
			onNodeUnselected: treeNodeUnSelect
		});
		
		tgt.data("viewdata", viewdata);	//bind the data to the div element
		tgt.data("treeview", tree);
	}).done(callafter);
};
