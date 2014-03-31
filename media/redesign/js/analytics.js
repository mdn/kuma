(function(win, doc, $) {
    'use strict';

    // Adding to globally available mdn object
    var analytics = mdn.analytics = {
        /*
            Tracks generic events passed to the method
        */
        trackEvent: function(eventArray, callback) {
            // Submit eventArray to GA and call callback only after tracking has
            // been sent, or if sending fails.
            //
            // callback is optional.
            //
            // Example usage:
            //
            // $(function() {
            //            var handler = function(e) {
            //                     var self = this;
            //                     e.preventDefault();
            //                     $(self).off('submit', handler);
            //                     gaTrack(
            //                            ['Newsletter Registration', 'submit'],
            //                            function() { $(self).submit(); }
            //                     );
            //            };
            //            $(thing).on('submit', handler);
            // });

            var _gaq = win._gaq;
            var timeout;
            var timedCallback;

            // Create the final event array
            if(eventArray[0] == '_trackEvent') { // legacy
                eventArray.shift();
            }
            eventArray  = ['_trackEvent'].concat(eventArray);

            // Create the timed callback if a callback function has been provided
            if (typeof(callback) == 'function') {
                timedCallback = function() {
                    clearTimeout(timeout);
                    callback();
                };
            }

            // If Analytics has loaded, go ahead wiht tracking
            if (_gaq && _gaq.push) {
                // Send event to GA
                _gaq.push(eventArray);
                // Only set up timeout and hitCallback if a callback exists.
                if (timedCallback) {
                    // Failsafe - be sure we do the callback in a half-second
                    // even if GA isn't able to send in our trackEvent.
                    timeout = setTimeout(timedCallback, 500);

                    // But ordinarily, we get GA to call us back immediately after
                    // it finishes sending our things.
                    // https://developers.google.com/analytics/devguides/collection/gajs/#PushingFunctions
                    // This is called after GA has sent the current pending data:
                    _gaq.push(timedCallback);
                }
            }
            else if(callback) {
                // GA disabled or blocked or something, make sure we still
                // call the caller's callback:
                callback();
            }
        },

        /*
            Track all outgoing links
        */
        trackOutboundLinks: function(target) {
            $(target).on('click', 'a', function (e) {
                var host = this.hostname;

                if(host && host != location.hostname) {
                    var newTab = (this.target == '_blank' || e.metaKey || e.ctrlKey);
                    var href = this.href;
                    var callback = function() {
                        location = href;
                    };
                    var data = ['Outbound Links', href];

                    if (newTab) {
                        analytics.trackEvent(data);
                    } else {
                        e.preventDefault();
                        analytics.trackEvent(data, callback);
                    }
                }
            });
        },

        /*
            Track Clientside errors
        */
        trackClientErrors: function() {
            $(win).on('error', function(e) {
                analytics.trackEvent([
                    'JavaScript error',
                    e.originalEvent.message,
                    e.originalEvent.filename + ':' + e.originalEvent.lineno
                ]);
            });
            $(doc).ajaxError(function(e, request, settings) {
                analytics.trackEvent([
                    'Ajax error',
                    settings.url,
                    e.result
                ]);
            });
        }
    };
})(window, document, jQuery);
