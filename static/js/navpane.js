// gets data to fill out the nav pane
var renderNavPane = function(callafter) {
	$.getJSON("/navdata", 
	function(data) {
		var tgt = $("#sidebar-nav");
		var viewdata = {};
		
		$.each(data, function(key, val) {
			viewdata[val.text] = val;
		});
		
		tgt.treeview({
			data: data
		});
		
		tgt.data("viewdata", viewdata);	//bind the data to the div element
	}).done(callafter);
};
