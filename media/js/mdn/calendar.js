var mapstraction;
var geocoder;
var address;
var locs = [];
var dates = [];
function initialize() {
  mapstraction = new Mapstraction('map_canvas','google');
  mapstraction.setCenterAndZoom(new LatLonPoint(50,0), 3);
  geocoder = new MapstractionGeocoder(geocode_return, 'google');
  mapstraction.addControls({pan:true,zoom:'small',map_type:true});
  var x = document.getElementById('upcoming');
  var rows = x.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
  for(var i=0;i<rows.length;i++){
    var loc = rows[i].getElementsByTagName('td')[2];
    dates.push(rows[i].getElementsByTagName('td')[0].innerHTML);
    var o = rows[i].innerHTML;
    geocoder.geocode({address:loc.innerHTML},o);
  }
}

function geocode_return(geocoded_location,o) {
  var marker = new Marker(geocoded_location.point);
  marker.setInfoBubble('<ul>'+o.replace(/td>/g,'li>')+'</ul>');
  mapstraction.addMarker(marker);
}

window.addEventListener('load',function(event){
  initialize();
},false);
