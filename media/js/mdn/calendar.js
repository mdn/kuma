$(function() {
    var markers = [];
    var address;
    $('#upcoming tbody tr').each(function(){
        var html = $(this).children('td.date').html() + "<br/>";
        html += $(this).children('td.conference').html() + "<br/>";
        var marker = {
            address: $(this).children('td.location').text(),
            icon: {
                image: "/media/img/icn-tool-mozilla.png",
                iconsize: [32, 26],
                iconanchor: [16, 13],
                infowindowanchor: [24, 0]
            },
            html: html,
        };
        markers.push(marker);
    });
    $('#map_canvas').gMap({longitude: 1, latitude: 10, markers: markers, zoom: 2});
    $('#upcoming').tablesorter({sortList:[[0,0]]});
    $('#past').tablesorter({sortList:[[0,0]]});
});
