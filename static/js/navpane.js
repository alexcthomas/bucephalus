// gets data to fill out the nav pane
var renderNavPane = function(callafter) {
	$.getJSON("/navdata", 
	function(data) {
		var tgt = $("#sidebar-nav");
		var viewdata = {};
		
		$.each(data, function(key, val) {
			if (val.title!="Root"){
				$('<li/>', {id: val.title})	// create a list element
					.append($('<a/>', {text: val.title, href: '#'}))	//add a link
					.appendTo(tgt);	// append to the nav pane
			}
			viewdata[val.title] = val;
		});
		tgt.data("viewdata", viewdata);	//bind the data to the list element
	}).done(callafter);
};
