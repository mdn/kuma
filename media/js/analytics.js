(function(win, doc, $) {
    'use strict';

    // Adding to globally available mdn object
    var analytics = mdn.analytics = {
        /*
            Tracks generic events passed to the method
        */
        trackEvent: function(eventObject, callback) {
            // Submit eventArray to GA and call callback only after tracking has
            // been sent, or if sending fails.
            //
            // callback is optional.

            /*
                Format:

                    ga('send', {
                        'eventCategory' : 'Star Trek',
                        'eventAction'   : 'Fire',
                        'eventLabel'    : 'Phasers',
                        'eventValue'    : 100,
                        'hitCallback'   : function () {
                            document.location = href;
                        },
                        'hitType': 'event'
                    });
            */

            var ga = win.ga;
            var data = {
                hitType: 'event',
                eventCategory: eventObject.category || '',    // Required.
                eventAction: eventObject.action || '',             // Required.
                eventLabel: eventObject.label || '',
                eventValue: eventObject.value || 0,
                hitCallback: callback || null
            };

            // If Analytics has loaded, go ahead with tracking
            // Checking for ".create" due to Ghostery mocking of ga
            if(ga && ga.create) {
                // Send event to GA
                ga('send', data);
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
            target = target || document.body;

            $(target).on('click', 'a', function (e) {
                var $this = $(this);

                // If we explicitly say not to track something, don't
                if($this.hasClass('no-track')) {
                    return;
                }

                var host = this.hostname;
                if(host && host !== location.hostname) {
                    var newTab = (this.target === '_blank' || e.metaKey || e.ctrlKey);
                    var href = this.href;
                    var callback = function() {
                        win.location = href;
                    };
                    var data = {
                        category: 'Outbound Links',
                        action: href
                    };

                    if(newTab) {
                        analytics.trackEvent(data);
                    } else {
                        e.preventDefault();
                        data.hitCallback = callback;
                        analytics.trackEvent(data, callback);
                    }
                }
            });
        },

        /*
            Track specific clientside errors create by our code
        */
        trackClientErrors: function() {
            $(win).on('error', function(e) {
                var originalEvent = e.originalEvent;
                analytics.trackError(' JavaScript Error: ' + originalEvent.message + ' ; ' + originalEvent.filename + ':' + originalEvent.lineno);
            });
            $(doc).ajaxError(function(e, request, settings) {
                analytics.trackError('AJAX Error: ' +  settings.url + ' : ' + e.result);
            });
        },

        /*
            Sends universal analytics client side error
        */
        trackError: function(category, action) {
            return analytics.trackEvent({
                category: category,
                action: action
            });
        }
    };
})(window, document, jQuery);
