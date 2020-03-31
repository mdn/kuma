/**
 * This file creates a global window.mdn.analytics object that defines
 * various functions that send data to google analytics. Some of these
 * functions are used on both the wiki domain and the new readonly domain.
 *
 * TODO: some of the functions here are unused on the readonly domain
 * so we should probably have a different, smaller, version of this file
 * for use on that domain. Ideally we should review the data we are sending
 * and if we still care about it, we should integrate the code into the
 * new React codebase.
 */
(function(win, doc) {
    'use strict';

    // Adding to globally available mdn object
    var analytics = mdn.analytics = {
        /**
         * Sets the value for a specific dimension.
         * For example setting dimension14 to Yes, means:
         * Saw Survey Gizmo Task Completion survey = Yes
         * @param {Object} data - The dimension data to set ex.
         * {
         *     dimension: 'dimension14',
         *     value: 'Yes'
         * }
         */
        setDimension: function(data) {
            if (win.ga) {
                win.ga('set', data.dimension, data.value);
            }
        },
        /**
         * Sends a statistic to GA dependant on the status of the win.ga object
         * @param {object} data - The data to send to GA
         * @param {function} [callback] - The function to call after sending data
         */
        send: function(data, callback) {
            var ga = win.ga;
            // If Analytics has loaded, go ahead with tracking
            // Checking for ".create" due to Ghostery mocking of ga
            if(ga && ga.create) {
                // Send event to GA
                ga('send', data);
                // execute callback now
                if(callback) {
                    callback();
                }
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
            var data = {
                hitType: eventObject.hitType || 'event',
                eventCategory: eventObject.category || '',    // Required.
                eventAction: eventObject.action || '',             // Required.
                eventLabel: eventObject.label || '',
                eventValue: eventObject.value || 0,
                hitCallback: callback || null
            };

            // task-completion.js sends an additional metric
            if(eventObject.nonInteraction !== undefined) {
                // append it to the data object sent to GA
                data.nonInteraction = eventObject.nonInteraction;
            }
            mdn.analytics.send(data, callback);
        },
        /**
         * Sends a timing event to GA
         * @param {object} timingObject - The timing data to send to GA
         */
        trackTiming: function(timingObject) {
            /*
                Format:
                    ga('send', {
                        'timingCategory' : 'JS Dependencies',
                        'timingVar'      : 'load',
                        'timingValue'    : 100,
                        'timingLabel'    : 'interactive-examples',
                        'hitCallback'   : function () {
                            document.location = href;
                        },
                        'hitType': 'timing'
                    });
            */
            var data = {
                hitType: 'timing',
                timingCategory: timingObject.category || '', // Required.
                timingVar: timingObject.timingVar || '', // Required.
                timingValue: timingObject.value ? Math.round(timingObject.value) : 0,  // Required.

            };

            // if a label has been passed and it is not simply an empty string
            if (timingObject.label && timingObject.label !== '') {
                // add to object to be sent to GA
                data['timingLabel'] = timingObject.label;
            }

            mdn.analytics.send(data);
        },

        trackLink: function(event, url, data) {
            // ctrl or cmd click or context menu
            var newTab = (event.metaKey || event.ctrlKey || event.type === 'contextmenu');
            // is a same page anchor
            var isAnchor = (url.indexOf('#') === 0);
            // isBlank
            var isBlank = event.target.target === '_blank';

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
            win.addEventListener('error', function(e) {
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

            // If the global jQuery object is defined, then we're on
            // the wiki site and are using jQuery, so we should track
            // any jQuery Ajax errors that occur. But if jQuery is not
            // defined, then we're on the new readonly site are not using
            // the jQuery Ajax library, so there is nothing to track
            if (win && win.jQuery) {
                jQuery(doc).ajaxError(function(e, request, settings) {
                    analytics.trackError('AJAX Error', settings.url, JSON.stringify({
                        result: e.result,
                        status: request.status,
                        statusText: request.statusText,
                        crossDomain: settings.crossDomain,
                        dataType: settings.dataType })
                    );
                });
            }
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

    /*
        Track all outgoing links
    */
    function trackOutboundLinks() {
        document.body.addEventListener('click', function(e) {

            var link = e.target.closest('a');
            if (!link) {
                // If the click was not on a link there is nothing to track
                return;
            }

            // bug 1222864 - prevent links to data: uris
            if (link.href.toLowerCase().indexOf('data') === 0) {
                e.preventDefault();
                analytics.trackError('XSS Attempt', 'data href');
                return;
            }

            // If we explicitly say not to track something, don't
            if (link.classList.contains('no-track')) {
                return;
            }

            var host = link.hostname;
            if(host && host !== location.hostname) {
                var newTab = (link.target === '_blank' || e.metaKey || e.ctrlKey);
                var href = link.href;
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
    }


    /* Some things we always trigger. */
    trackOutboundLinks();

})(window, document);
