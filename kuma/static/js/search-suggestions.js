(function(win, doc, $) {
    'use strict';

    var noop = function() {};

    var removeAccents = function(str) {
        var map = {'\xc0': 'A', '\xc1': 'A', '\xc2': 'A', '\xc3': 'A', '\xc4': 'A', '\xc5': 'A', '\xc6': 'AE', '\xc7': 'C', '\xc8': 'E', '\xc9': 'E', '\xca': 'E', '\xcb': 'E', '\xcc': 'I', '\xcd': 'I', '\xce': 'I', '\xcf': 'I', '\xd0': 'D', '\xd1': 'N', '\xd2': 'O', '\xd3': 'O', '\xd4': 'O', '\xd5': 'O', '\xd6': 'O', '\xd8': 'O', '\xd9': '', '\xda': '', '\xdb': '', '\xdc': '', '\xdd': 'Y', '\xdf': 's', '\xe0': 'a', '\xe1': 'a', '\xe2': 'a', '\xe3': 'a', '\xe4': 'a', '\xe5': 'a', '\xe6': 'ae', '\xe7': 'c', '\xe8': 'e', '\xe9': 'e', '\xea': 'e', '\xeb': 'e', '\xec': 'i', '\xed': 'i', '\xee': 'i', '\xef': 'i', '\xf1': 'n', '\xf2': 'o', '\xf3': 'o', '\xf4': 'o', '\xf5': 'o', '\xf6': 'o', '\xf8': 'o', '\xf9': '', '\xfa': '', '\xfb': '', '\xfc': '', '\xfd': 'y', '\xff': 'y', '\u0100': 'A', '\u0101': 'a', '\u0102': 'A', '\u0103': 'a', '\u0104': 'A', '\u0105': 'a', '\u0106': 'C', '\u0107': 'c', '\u0108': 'C', '\u0109': 'c', '\u010a': 'C', '\u010b': 'c', '\u010c': 'C', '\u010d': 'c', '\u010e': 'D', '\u010f': 'd', '\u0110': 'D', '\u0111': 'd', '\u0112': 'E', '\u0113': 'e', '\u0114': 'E', '\u0115': 'e', '\u0116': 'E', '\u0117': 'e', '\u0118': 'E', '\u0119': 'e', '\u011a': 'E', '\u011b': 'e', '\u011c': 'G', '\u011d': 'g', '\u011e': 'G', '\u011f': 'g', '\u0120': 'G', '\u0121': 'g', '\u0122': 'G', '\u0123': 'g', '\u0124': 'H', '\u0125': 'h', '\u0126': 'H', '\u0127': 'h', '\u0128': 'I', '\u0129': 'i', '\u012a': 'I', '\u012b': 'i', '\u012c': 'I', '\u012d': 'i', '\u012e': 'I', '\u012f': 'i', '\u0130': 'I', '\u0131': 'i', '\u0132': 'IJ', '\u0133': 'ij', '\u0134': 'J', '\u0135': 'j', '\u0136': 'K', '\u0137': 'k', '\u0139': 'L', '\u013a': 'l', '\u013b': 'L', '\u013c': 'l', '\u013d': 'L', '\u013e': 'l', '\u013f': 'L', '\u0140': 'l', '\u0141': 'L', '\u0142': 'l', '\u0143': 'N', '\u0144': 'n', '\u0145': 'N', '\u0146': 'n', '\u0147': 'N', '\u0148': 'n', '\u0149': 'n', '\u014c': 'O', '\u014d': 'o', '\u014e': 'O', '\u014f': 'o', '\u0150': 'O', '\u0151': 'o', '\u0152': 'OE', '\u0153': 'oe', '\u0154': 'R', '\u0155': 'r', '\u0156': 'R', '\u0157': 'r', '\u0158': 'R', '\u0159': 'r', '\u015a': 'S', '\u015b': 's', '\u015c': 'S', '\u015d': 's', '\u015e': 'S', '\u015f': 's', '\u0160': 'S', '\u0161': 's', '\u0162': 'T', '\u0163': 't', '\u0164': 'T', '\u0165': 't', '\u0166': 'T', '\u0167': 't', '\u0168': '', '\u0169': '', '\u016a': '', '\u016b': '', '\u016c': '', '\u016d': '', '\u016e': '', '\u016f': '', '\u0170': '', '\u0171': '', '\u0172': '', '\u0173': '', '\u0174': 'W', '\u0175': 'w', '\u0176': 'Y', '\u0177': 'y', '\u0178': 'Y', '\u0179': 'Z', '\u017a': 'z', '\u017b': 'Z', '\u017c': 'z', '\u017d': 'Z', '\u017e': 'z', '\u017f': 's', '\u0192': 'f', '\u01a0': 'O', '\u01a1': 'o', '\u01af': '', '\u01b0': '', '\u01cd': 'A', '\u01ce': 'a', '\u01cf': 'I', '\u01d0': 'i', '\u01d1': 'O', '\u01d2': 'o', '\u01d3': '', '\u01d4': '', '\u01d5': '', '\u01d6': '', '\u01d7': '', '\u01d8': '', '\u01d9': '', '\u01da': '', '\u01db': '', '\u01dc': '', '\u01fa': 'A', '\u01fb': 'a', '\u01fc': 'AE', '\u01fd': 'ae', '\u01fe': 'O', '\u01ff': 'o'};
        var val = '';
        for (var i = 0; i < str.length; i++) {
            var c = str.charAt(i);
            val += map[c] || c;
        }
        return val;
    };

    $.fn.searchSuggestions = function(options) {
        return $(this).each(function() {

            // Save me so we don't run into "this" issues
            var $form = $(this);

            // Mixin options
            var settings = $.extend({
                sizeLimit: 25,
                filters: null,
                onAddFilter: noop,
                onRemoveFilter: noop,
            }, options);

            var $searchForm = $form.find('.search-form');
            var $searchFilters = $('#home-search-form .filters');
            var $showTopics = $('.show-topics');
            var $searchInput = $('#home-q');
            var $rightColumFilters = $('.search-results-filters input');

            var $suggestions = $('<ul></ul>')
                .addClass('suggestions')
                .data('hidden', 'true')
                .css('display', 'none')
                .appendTo($searchForm);

            // Private vars we'll use throughout the course of the plugin lifecycle
            var filtersData = win.mdn.searchFilters || [];
            var BASE_SEARCH_URL = $form.attr('action');
            var previousValue = $searchInput.val();
            var populated;

            var fnSuggestions = {
                prepareInput: function() {
                    this.storeSize(settings.sizeLimit);
                },
                storeSize: function(size) {
                    $searchInput.attr('size', size || $searchInput.val().length < settings.sizeLimit ? settings.sizeLimit : $searchInput.val().length);
                },
                parse: function(s) {
                    var matches = s.match(/^(#\S+)\s+|\s(#\S+)\s+/);
                    return matches ? matches[1] || matches[2] : matches;
                },
                open: function() {
                    $suggestions.attr('data-hidden', 'false');
                    $suggestions.slideDown();
                },
                close: function() {
                    $suggestions.attr('data-hidden', 'true');
                    $suggestions.slideUp();
                },
                populate: function() {
                    if ($suggestions.attr('data-hidden') === 'false') {
                        var fs = $searchInput.val().match(/#(\S+)/) || [];
                        this.recoverTopics(fs[1] || '');

                        if (!populated) {
                            // Add keyboard navigation for the filters
                            $('.search').mozKeyboardNav({
                                alwaysCollectItems: true
                            });
                            populated = true;
                        }
                    }
                },
                addFilter: function(slug, group, shortcut) {
                    shortcut = shortcut || slug;
                    var self = this;
                    var filter = $('<span></span>')
                        .addClass('topic button')
                        .attr('data-topic', slug)
                        .attr('data-group', group)
                        .text('#' + shortcut)
                        .appendTo($searchFilters);

                    $('<button></button>')
                        .addClass('close')
                        .attr('type', 'button')
                        .html('<i aria-hidden="true" class="icon-remove"></i>')
                        .on('click', function() {
                            $(filter).remove();
                            $.each(filtersData, function(index, groupFilters) {
                                if (groupFilters.slug === group) {
                                    $.each(groupFilters.filters, function(index, filter) {
                                        if (typeof(filter) !== 'undefined' && filter.slug === slug) {
                                            filter.shortcut = shortcut;
                                            self.close();
                                        }
                                    });
                                }
                            });
                        })
                    .appendTo(filter);
                },
                parseAndAddFilters: function() {
                    var toParse = $searchInput.val();
                    var filter = true;
                    var filters = [];
                    var self = this;
                    while (filter) {
                        filter = self.parse(toParse);
                        if (filter) {
                            filters.push(filter);
                            toParse = toParse.replace(filter, '').trim();
                        }
                    }

                    if (filters.length >= 1) {
                        filters.forEach(function(entry) {
                            $.each(filtersData, function(idx_group, group) {
                                var groupSlug = group.slug;
                                $.each(group.filters, function(idx_filter, filter) {
                                    if (typeof(filter) !== 'undefined' && (filter.shortcut || filter.slug) === entry.replace('#', '')) {
                                        self.addFilter(filter.slug, groupSlug, filter.shortcut);
                                        filtersData[idx_group].filters[idx_filter].shortcut = 'hidden';
                                    }
                                });
                            });
                        });
                        self.close();
                    }

                    $searchInput.val(toParse);
                    this.storeSize();
                },
                removeFilterFromList: function(slug) {
                    $.each(filtersData, function(idx_group, group) {
                        $.each(group.filters, function(idx_filter, filter) {
                            if (typeof(filter) !== 'undefined' && filter.slug === slug) {
                                filtersData[idx_group].filters[idx_filter].shortcut = 'hidden';
                            }
                        });
                    });
                },
                recoverTopics: function(f) {
                    // clean suggestion div
                    $suggestions.empty();
                    var self = this;
                    $.each(filtersData, function(index, group) {
                        var title = $('<strong>').text(group.name);
                        var groupSlug = group.slug;
                        var $ul = $('<ul></ul>');
                        var show = false;
                        $.each(group.filters, function(index, filter) {
                            var filterSlug = filter.shortcut || filter.slug;
                            var slugNorm = filterSlug.toLowerCase();
                            var nameNorm = removeAccents(filter.name.toLowerCase());
                            if ((!f || slugNorm.indexOf(removeAccents(f.toLowerCase())) !== -1 || nameNorm.indexOf(removeAccents(f.toLowerCase())) !== -1) && filter.shortcut !== 'hidden') {
                                var $li = $('<li></li>')
                                    .attr('data-slug', filter.slug)
                                    .addClass('sug');
                                $('<a></a>')
                                    .attr('class', 'search-ss')
                                    .attr('href', '#')
                                    .html(filter.name + ' <span>#' + filterSlug + '</span>')
                                    .appendTo($li)
                                    .on('click', function(e) {
                                        e.preventDefault();
                                        self.addFilter(filter.slug, groupSlug, filter.shortcut);
                                        $searchInput.val($searchInput.val().replace('#' + f, ''));
                                        previousValue = $searchInput.val();
                                        self.storeSize();
                                        $suggestions.attr('data-hidden', 'true');
                                        $suggestions.hide();
                                        self.removeFilterFromList(filter.slug);
                                        $searchInput.focus();
                                    });
                                $li.appendTo($ul);
                                show = true;
                            }
                        });
                        if (show) {
                            $suggestions.append(title);
                            $suggestions.append($ul);
                        }
                    });
                }
            };

            // prepare input
            fnSuggestions.prepareInput();

            // load previouly selected filters
            if (settings.filters !== null) {
                $.each(settings.filters, function(sidx, sfilter) {
                    // foreach filters to get the correct shortcut
                    $.each(filtersData, function(index, group) {
                        if (group.slug === sfilter.group) {
                            $.each(group.filters, function(index, filter) {
                                if (typeof(filter) !== 'undefined' && filter.slug === sfilter.slug) {
                                    fnSuggestions.addFilter(sfilter.slug, sfilter.group, filter.shortcut);
                                    fnSuggestions.removeFilterFromList(sfilter.slug);
                                }
                            });
                        }
                    });
                });
            } else {
                var filterDefaults = $searchFilters.data('default');
                $.each(filterDefaults, function(i, tuple) {
                    // The tuple is [<group slug>, <filter slug>, <shortcut>]
                    fnSuggestions.addFilter(tuple[1], tuple[0], tuple[2]);
                    fnSuggestions.removeFilterFromList(tuple[1]);
                });
            }

            // events
            $searchForm.on('click', function() {
                $searchInput.focus();
            });


            $searchInput.on('input', function() {
                fnSuggestions.storeSize();
                fnSuggestions.parseAndAddFilters();

                // find out if there is a difference of exactly one # between input.value and previousValue
                // Current algorithm is very simple. Must be improved in the future
                // Currently consider only the last character
                if ($searchInput.val().length - previousValue.length === 1 && $searchInput.val()[$searchInput.val().length - 1] === '#') {
                    fnSuggestions.open();
                } else if (previousValue.length - $searchInput.val().length === 1 && previousValue[previousValue.length - 1] === '#') {
                    fnSuggestions.close();
                }

                fnSuggestions.populate();

                previousValue = $searchInput.val();
            });

            $showTopics.on('click', function(e) {
                e.preventDefault();
                if ($suggestions.attr('data-hidden') === 'false') {
                    fnSuggestions.close();
                } else {
                    fnSuggestions.open();
                    fnSuggestions.populate();
                }
            });

            $rightColumFilters.on('change', function() {
                var rslug = $(this).val();
                var rgroup = $(this).attr('name');
                var rshortcut = '';
                if ($(this).is(':checked')) {
                    // Need to foreacht to recover the filter shortcut
                    $.each(filtersData, function(idx_group, group) {
                        $.each(group.filters, function(idx_filter, filter) {
                            if (typeof(filter) !== 'undefined' && filter.slug === rslug) {
                                rshortcut = filter.shortcut;
                            }
                        });
                    });

                    fnSuggestions.addFilter(rslug, rgroup, rshortcut);
                    fnSuggestions.removeFilterFromList(rslug);
                } else {
                    $searchFilters.find('[data-topic="' + rslug + '"]').remove();
                }
            });

            $form.on('submit', function(e) {
                e.preventDefault();

                var topics = $.makeArray($form.find('.topic')).map(function(e) {
                    var topic = {
                        'filter': $(e).data('topic'),
                        'group': $(e).data('group')
                    };
                    return topic;
                });
                var topicsString = topics.map(function(t) {
                    return t.group + '=' + t.filter;
                }).join('&');
                var searchQuery = encodeURIComponent($searchInput.val());

                // Redirects to search
                location.href = BASE_SEARCH_URL + '?' + 'q=' + searchQuery +
                    (topicsString ? '&' + topicsString : '');
            });

        });
    };

})(window, document, jQuery);
