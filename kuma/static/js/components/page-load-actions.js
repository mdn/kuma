/**
 * Actions that should happen during various stages
 * during page load
 */
window.addEventListener('load', function() {
    var hash = window.location.hash;
    /* if the doument url contains a hash,
       find the element with an `id` matching
       the hash, and scroll to it */
    if (hash) {
        var id = hash.substr(1);
        var elem = document.getElementById(id);
        if (elem) {
            /* Firefox ignores whatever value is passed to
               `scroll` if called immediately on `load`, so,
               wait for 60ms before calling the function */
            setTimeout(function() {
                mdn.utils.scrollToHeading(id);
            }, 60);
        }
    }
});
