(function(win, doc, $) {
    'use strict';

    // Adding to globally available mdn object
    var analytics = mdn.analytics = {
        /**
         * Handles postMessage events from the interactive editor, passing of
         * the data to `trackEvent` if the origin of the message is what we expect.
         * @param {Object} event - The event Object received from the postMessage
         */
        interactiveExamplesEvent: function(event) {
            var allowedOrigin = win.mdn.interactiveEditor.editorUrl || 'https://interactive-examples.mdn.mozilla.net';
            if (event.origin !== allowedOrigin) {
                return false;
            }
            mdn.analytics.trackEvent(event.data);
        },
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
            else if(ga && !ga.create) {
                // GA blocked or not yet initialized
                // strip callback from data
                data.hitCallback = null;
                // add to queue without callback
                ga('send', data);
                // execute callback now
                if(callback) {
                    callback();
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
            target = target || document.body;

            $(target).on('click', 'a', function (e) {
                var $this = $(this);

                // bug 1222864 - prevent links to data: uris
                if (this.href.toLowerCase().indexOf('data') === 0) {
                    e.preventDefault();
                    analytics.trackError('XSS Attempt', 'data href');
                    return;
                }

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

        trackLink: function(event, url, data) {
            // ctrl or cmd click or context menu
            var newTab = (event.metaKey || event.ctrlKey || event.type === 'contextmenu');
            // is a same page anchor
            var isAnchor = (url.indexOf('#') === 0);
            // isBlank
            var isBlank = $(event.target).attr('target') === '_blank';

            if(newTab || isAnchor || isBlank) {
                mdn.analytics.trackEvent(data);
            }
            else {
                event.preventDefault();
                mdn.analytics.trackEvent(data, function() {
                    window.location = url;
                });
            }
        },

        /*
            Track specific clientside errors created by our code
            this article was a lot of help: http://blog.gospodarets.com/track_javascript_angularjs_and_jquery_errors_with_google_analytics/
        */
        trackClientErrors: function() {

            // javascript & jQuery errors
            $(win).on('error', function(e) {
                // probably javascript
                if(e.originalEvent) {
                    var originalEvent = e.originalEvent;
                    var lineAndColumnInfo = originalEvent.colno ? ' line:' + originalEvent.lineno +', column:'+ originalEvent.colno : ' line:' + originalEvent.lineno;
                    analytics.trackError('JavaScript Error', originalEvent.message , originalEvent.filename + ':' + lineAndColumnInfo);
                }
                // no originalEvent means probably jQuery
                else {
                    var message = e.message ? e.message : '';
                    analytics.trackError('jQuery Error', message);
                }
            });

            // jQuery ajax errors
            $(doc).ajaxError(function(e, request, settings) {
                analytics.trackError('AJAX Error', settings.url , JSON.stringify({
                    result: e.result,
                    status: request.status,
                    statusText: request.statusText,
                    crossDomain: settings.crossDomain,
                    dataType: settings.dataType })
                );
            });
        },

        /*
            Sends universal analytics client side error
        */
        trackError: function(category, action, label) {
            // label is optional, give it a default value if it's not passed
            label = typeof label !== 'undefined' ? label : '';
            return analytics.trackEvent({
                'category': category,
                'action': action,
                'label': label
            });
        }
    };
    // add event listener for postMessages from the interactive editor
    win.addEventListener('message', analytics.interactiveExamplesEvent, false);
})(window, document, jQuery);
