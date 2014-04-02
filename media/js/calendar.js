$(document).ready(function() {

    var markers = [];
    var $mapCanvas = $('#map_canvas');
    var address;

    $('#upcoming tbody tr').each(function(){
        var $self = $(this);
        var html = $self.children('td.date').html() + '<br/>' + $self.children('td.conference').html() + '<br/>';

        // Add the new marker
        markers.push({
            address: $self.children('td.location').text(),
            icon: {
                image: '/media/img/icn-tool-mozilla.png',
                iconsize: [32, 26],
                iconanchor: [16, 13],
                infowindowanchor: [24, 0]
            },
            html: html
        });
    });

    // Start rendering the map with a default position.
    $mapCanvas.gMap({ longitude: 1, latitude: 10, markers: markers, zoom: 2 });

    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(function (position) {
            // If we're able and permitted to access position, move the map
            // center and zoom in a bit.
            var coords = position.coords;
            $mapCanvas.data('gmap').setCenter(new GLatLng(coords.latitude, coords.longitude), 4);
        });
    }

});
