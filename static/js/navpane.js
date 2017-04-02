// gets data to fill out the nav pane
$(function () {
	$(document).ready(function () {
		$.getJSON( "/navdata", 
		function( data ) {
			var tgt = $("#sidebar-nav");
			$.each( data, function( key, val ) {
				$('<li/>', {id: val.title})	// create a list element
					.append($('<a/>', {text: val.title, href: '#'}))	//add a link
					.data(val)	//bind the data to the list element
					.appendTo(tgt); // append to the nav pane
			});
		});
	});
});
