/* Adds delay on hiding submenu */
// Use closure to avoid globals
(function () {
var HIDE_TIMEOUT = 750,  // hide timeout, in milliseconds
    SHOWING = 'sfhover', // CSS class for showing submenu
    showing = null,      // reference to last parent showing its submenu
    timeout = null;      // reference to timeout event from setTimeout

    $('#nav-main > ul > li').mouseover(function () {
        // Ensures only one submenu displays
        if (null !== showing) {
            showing.removeClass(SHOWING);
            showing = null;
            clearTimeout(timeout);
        }
        // Fixes drop downs not showing on IE6
        $(this).addClass(SHOWING);
    }).mouseout(function () {
        showing = $(this);
        showing.addClass(SHOWING);
        // Hide submenu HIDE_TIMEOUT ms
        timeout = setTimeout(function () {
            showing.removeClass(SHOWING);
            showing = null;
        }, HIDE_TIMEOUT);
    });
}());
