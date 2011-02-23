$(document).ready(function(){
    $("#slide-control a").focus(function(){ window.focus(this); }); // corrects some weirdness with the slide show bogarting focus and breaking keyboard tabbing through links
});

$(document).ready(function(){
  var cabinets = Array();
  var collection = document.getElementsByTagName( '*' );
  var cLen = collection.length;
  for( var i=0; i<cLen; i++ ){
    if( collection[i] &&
        /\s*tabbed\s*/.test( collection[i].className ) ){
      cabinets.push( new TabInterface( collection[i], i ) );
    }
  }
});
