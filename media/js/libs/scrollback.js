/* global document, window, setTimeout*/
/* exported addScrollback */

(function(win, doc, jQuery) {

    // Open Scrollback upon button click
    $('.scrollback-button').on('click', function() {
        var $this = $(this);

        addScrollback($this.attr('data-room'), $this.attr('data-username'));
    });

    // Functionality for opening the Scrollback widget
    function addScrollback(roomName, suggestedNick) {

        var host  = 'https://scrollback.io/';

        if(!win.scrollback) {
            win.scrollback = {
                room: roomName,
                form: 'toast',
                titlebarColor: '#00539f',
                minimize: false,
                nick: suggestedNick || 'guest'
            };

            $.getScript(host + 'client.min.js');
        }
        else {
            $('.scrollback-stream').attr('src', function() {
                return $(this).attr('src').replace(host, '') + roomName;
            });
        }
    }

})(window, document, jQuery);
