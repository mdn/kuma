(function($) {
    'use strict';

    var analyticsCategory = 'Search doc navigator';

    /*
        Set up the "from search" buttons if user came from search
    */
    var fromSearchNav = $('.from-search-navigate');
    if(fromSearchNav.length) {
        var fromSearchList = $('.from-search-toc');
        fromSearchNav.mozMenu({
            submenu: fromSearchList,
            brickOnClick: true,
            onOpen: function(){
                mdn.analytics.trackEvent([analyticsCategory, 'Open on hover']);
            },
            onClose: function() {
                mdn.analytics.trackEvent([analyticsCategory, 'Close on blur']);
            }
        });
        fromSearchList.find('ol').mozKeyboardNav();
    }

    /*
        Auto-submit the filters form on the search page when a checkbox is changed.
    */
    $('.search-results-filters').on('change', 'input', function(event) {
        $('#search-form').submit();
        $(this).parents('fieldset').attr('disabled', 'disabled');
    });

    /*
        Set up the storage object Doc Navigator usage
    */
    var storage = (function() {
        var prefix = 'mdn.search';
        var keys = ['key', 'data'];

        var getKey = function(name) {
            return prefix + '.' + name;
        };

        return {
            flush: function() {
                var self = this;
                $.each(keys, function(index, key) {
                    self.removeItem(key);
                });
            },
            serialize: function(value) {
                return JSON.stringify(value);
            },
            deserialize: function(value) {
                if(typeof value != 'string') {
                    return undefined;
                }
                try {
                    return JSON.parse(value);
                } catch(e) {
                    return value || undefined;
                }
            },
            getItem: function(key) {
                return this.deserialize(sessionStorage.getItem(getKey(key)));
            },
            setItem: function(key, value) {
                return sessionStorage.setItem(getKey(key), this.serialize(value));
            },
            removeItem: function(key) {
                return sessionStorage.removeItem(getKey(key));
            }
        };
    })();

    // Flush out the navigator data if requested
    if($('body').hasClass('search-navigator-flush')) {
        storage.flush();
    }

    /*
        Create the search results plugin
    */
    $.fn.mozSearchResults = function(url) {
        var next_doc;
        var prev_doc;
        var data;
        var url = url;
        var key = storage.getItem('key');

        // Get out of town if no URL and no key
        if(!key && !url) {
            return;
        }

        var populate = function(data) {
            var slug = $('body').data('slug');
            var found = false;

            // setting the main search input with the store query
            if(data && data.query) {
                $('#main-q').val(data.query);
            }

            // First walk the loaded documents
            if(data.documents.length) {

                // Before we go into processing, let's ensure that *this* page's slug is in the list
                $.each(data.documents, function() {
                    if(this.slug == slug) {
                        found = true;
                    }
                });

                // If the current page doesn't match the list, get out
                if(!found) return;

                // Show the up/down navigator icon
                $('.from-search-navigate-wrap').removeClass('hidden');

                // Since we know the navigator should display, generate the HTML and show the navigation
                $.each(data.documents, function(index, doc) {

                    var link = $('<a>', {
                        text: doc.title,
                        href: doc.url,
                        on: {
                            click: function() {
                                mdn.analytics.trackEvent([analyticsCategory, 'Click', $(this).attr('href'), doc.id]);
                            }
                        }
                    });

                    if(doc.slug == slug) {
                        link.addClass('current');

                        // see if we can find the next page in the loaded documents
                        next_doc = data.documents[index+1];
                        if(next_doc) {
                            // and set the href of the next page anchor, make it visible, too
                            $('.from-search-next').each(function() {
                                $(this).attr('href', next_doc.url)
                                     .on('click', function() {
                                            mdn.analytics.trackEvent([analyticsCategory, 'Click next', next_doc.url, next_doc.id]);
                                     })
                                     .parent()
                                     .removeClass('hidden');
                            });
                        }

                        // do the same for the previous page link
                        prev_doc = data.documents[index-1];
                        if(prev_doc) {
                            $('.from-search-previous').each(function() {
                                $(this).attr('href', prev_doc.url)
                                     .on('click', function() {
                                            mdn.analytics.trackEvent([analyticsCategory, 'Click previous', prev_doc.url, prev_doc.id]);
                                     })
                                     .parent()
                                     .addClass('from-search-spacer') // also add a spacer
                                     .removeClass('hidden');
                            });
                        }
                    }

                    // Append new navigator item to the list
                    $('.from-search-toc ol').append($('<li></li>').append(link));
                });

                // Display the search navigator
                $('#wiki-document-head').addClass('from-search');
            }
        };

        // Set in motion the process to show and populate or hide the navigator!
        if(!url) {
            if(key) {
                url = key
            }
        }
        else {
            storage.setItem('key', url);
        }
        data = storage.getItem('data');
        if(!data) {
            $.ajax({
                url: url,
                dataType: 'json',
                success: function(data) {
                    storage.setItem('data', data);
                    populate(data);
                },
                error: function(xhr, status, err) {
                    console.error(url, status, err.toString());
                }
            });
        } else {
            populate(data);
        }
        return this;
    };

})(jQuery);
