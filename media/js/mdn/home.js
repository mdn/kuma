$(document).ready(function(){
	// corrects some weirdness with the slide show bogarting focus and breaking keyboard tabbing through links
	$("#slide-control a").focus(function(){ window.focus(this); }); 

	// Create any tabbed interface as necessary
	$(".tabbed").each(function(index) {
		new TabInterface(this, index);
	});
});