/*

    To Do:

        1. Show the next and prev buttons regardless of next/prev doc presence
            add a "disabled" class if the button shouldn't be there.

*/

(function($) {
    'use strict';

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
                if(typeof value !== 'string') {
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

    /*
        Flush out the navigator data if requested
    */
    if($('body').hasClass('search-navigator-flush')) {
        storage.flush();
    }

    /*
        Create the search results plugin
    */
    $.fn.mozSearchResults = function(url) {
        var key = storage.getItem('key');
        var $nextLink = $('.from-search-next');
        var $prevLink = $('.from-search-previous');

        var nextDoc;
        var prevDoc;
        var data;

        // Get out of town if no URL and no key
        if(!key && !url) {
            return;
        }

        var populate = function(data) {
            // Get out if the data isnt complete
            if(!data || !data.documents || !data.documents.length) {
                return;
            }

            var pageSlug = $('body').data('slug');
            var listFrag = document.createDocumentFragment();
            var found;
            var $navigatorList;

            // Setting the main search input with the store query
            if(data.query) {
                $('#main-q').attr('data-value', data.query);
            }

            // Before we go into processing, let's ensure that *this* page's slug is in the list
            $.each(data.documents, function() {
                if(this.slug === pageSlug) {
                    found = this.slug;
                }
            });

            // If the current page doesn't match the list, get out
            if(!found) return;

            // Show the up/down navigator icon
            $('.from-search-navigate-wrap').removeClass('hidden');

            // Add a delegation event for link clicks in the naviagotr
            $navigatorList = $('.from-search-toc ol');
            $navigatorList.on('click', 'a', function() {
                mdn.analytics.trackEvent({
                    category: 'Search doc navigator',
                    action: 'Click',
                    label: $(this).attr('href'),
                    value: found
                });
            });

            // Since we know the navigator should display, generate the HTML and show the navigation
            $.each(data.documents, function(index, doc) {

                var link = $('<a>', {
                    text: doc.title,
                    href: doc.url
                });

                if(doc.slug === pageSlug) {
                    link.addClass('current');

                    // see if we can find the next page in the loaded documents
                    nextDoc = data.documents[index+1];
                    if(nextDoc) {
                        // and set the href of the next page anchor, make it visible, too
                        $nextLink
                            .attr('href', nextDoc.url)
                            .on('click', function() {
                                mdn.analytics.trackEvent({
                                    category: 'Search doc navigator',
                                    action: 'Click next',
                                    label: nextDoc.url,
                                    value: nextDoc.id
                                });
                            })
                            .removeClass('disabled');
                    }
                    else {
                        $nextLink.attr('title', $nextLink.attr('data-empty-title'));
                    }

                    // do the same for the previous page link
                    prevDoc = data.documents[index-1];
                    if(prevDoc) {
                        $prevLink
                            .attr('href', prevDoc.url)
                            .on('click', function() {
                                mdn.analytics.trackEvent({
                                    category: 'Search doc navigator',
                                    action: 'Click previous',
                                    label: prevDoc.url,
                                    value: prevDoc.id
                                });
                            })
                            .removeClass('disabled'); // also add a spacer
                    }
                    else {
                        $prevLink.attr('title', $nextLink.attr('data-empty-title'));
                    }
                }

                // Append new navigator item to the list
                listFrag.appendChild($('<li></li>').append(link).get(0));
            });

            //  Append all items to the list
            $navigatorList.append(listFrag);

            // Display the search navigator
            $('#wiki-document-head').addClass('from-search');
        };

        // Set in motion the process to show and populate or hide the navigator!
        if(!url) {
            if(key) {
                url = key;
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
