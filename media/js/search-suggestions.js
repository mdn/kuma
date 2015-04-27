(function(win, doc, $) {
    'use strict';

    var noop = function() { };

    $.fn.searchSuggestions = function(options) {
        return $(this).each(function() {

            // Save me so we don't run into "this" issues
            var $form = $(this);

            // Mixin options
            var settings = $.extend({
                sizeLimit: 25,
                filters: false,
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
                    if($suggestions.attr('data-hidden') == 'false') {
                        var fs = $searchInput.val().match(/#(\S+)/) || [];
                        this.recoverTopics(fs[1] || '');

                        if(!populated) {
                            // Add keyboard navigation for the filters
                            $('.search').mozKeyboardNav({
                                alwaysCollectItems: true
                            });
                            populated = true;
                        }
                    }
                },
                addFilter: function(slug, group, shortcut) {
                    var self = this;
                    var shortcut = (shortcut || slug);
                    var filter = $('<span></span>')
                        .addClass('topic button')
                        .attr('data-topic', slug)
                        .attr('data-group', group)
                        .text('#'+shortcut)
                        .appendTo($searchFilters);

                    $('<button></button>')
                        .addClass('close')
                        .attr('type', 'button')
                        .html('<i aria-hidden="true" class="icon-remove"></i>')
                        .on('click', function() {
                            $(filter).remove();
                            $.each(filtersData, function(index, groupFilters){
                                if(groupFilters.slug === group){
                                    $.each(groupFilters.filters, function(index, filter){
                                        if(typeof(filter) !== 'undefined' && filter.slug === slug) {
                                            filter.shortcut = shortcut;
                                            self.close();
                                        }
                                    });
                                }
                            });
                        })
                    .appendTo(filter)
                    //.focus();
                },
                parseAndAddFilters: function() {
                    var toParse = $searchInput.val();
                    var filter = true;
                    var filters = [];
                    var self = this;
                    while(filter) {
                        filter = self.parse(toParse);
                        if(filter) {
                            filters.push(filter);
                            toParse = toParse.replace(filter, '').trim();
                        }
                    }

                    if(filters.length >= 1){
                        filters.forEach(function(entry) {
                            $.each(filtersData, function(idx_group, group) {
                                var groupSlug = group.slug;
                                $.each(group.filters, function(idx_filter, filter) {
                                    if(typeof(filter) !== 'undefined' && (filter.shortcut || filter.slug) === entry.replace('#','')){
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
                removeAccents: function(srt) {
                    var map = {'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A', 'Æ': 'AE', 'Ç': 'C', 'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E', 'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I', 'Ð': 'D', 'Ñ': 'N', 'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O', 'Ø': 'O', 'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U', 'Ý': 'Y', 'ß': 's', 'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a', 'æ': 'ae', 'ç': 'c', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i', 'ñ': 'n', 'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'ø': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ý': 'y', 'ÿ': 'y', 'Ā': 'A', 'ā': 'a', 'Ă': 'A', 'ă': 'a', 'Ą': 'A', 'ą': 'a', 'Ć': 'C', 'ć': 'c', 'Ĉ': 'C', 'ĉ': 'c', 'Ċ': 'C', 'ċ': 'c', 'Č': 'C', 'č': 'c', 'Ď': 'D', 'ď': 'd', 'Đ': 'D', 'đ': 'd', 'Ē': 'E', 'ē': 'e', 'Ĕ': 'E', 'ĕ': 'e', 'Ė': 'E', 'ė': 'e', 'Ę': 'E', 'ę': 'e', 'Ě': 'E', 'ě': 'e', 'Ĝ': 'G', 'ĝ': 'g', 'Ğ': 'G', 'ğ': 'g', 'Ġ': 'G', 'ġ': 'g', 'Ģ': 'G', 'ģ': 'g', 'Ĥ': 'H', 'ĥ': 'h', 'Ħ': 'H', 'ħ': 'h', 'Ĩ': 'I', 'ĩ': 'i', 'Ī': 'I', 'ī': 'i', 'Ĭ': 'I', 'ĭ': 'i', 'Į': 'I', 'į': 'i', 'İ': 'I', 'ı': 'i', 'Ĳ': 'IJ', 'ĳ': 'ij', 'Ĵ': 'J', 'ĵ': 'j', 'Ķ': 'K', 'ķ': 'k', 'Ĺ': 'L', 'ĺ': 'l', 'Ļ': 'L', 'ļ': 'l', 'Ľ': 'L', 'ľ': 'l', 'Ŀ': 'L', 'ŀ': 'l', 'Ł': 'L', 'ł': 'l', 'Ń': 'N', 'ń': 'n', 'Ņ': 'N', 'ņ': 'n', 'Ň': 'N', 'ň': 'n', 'ŉ': 'n', 'Ō': 'O', 'ō': 'o', 'Ŏ': 'O', 'ŏ': 'o', 'Ő': 'O', 'ő': 'o', 'Œ': 'OE', 'œ': 'oe', 'Ŕ': 'R', 'ŕ': 'r', 'Ŗ': 'R', 'ŗ': 'r', 'Ř': 'R', 'ř': 'r', 'Ś': 'S', 'ś': 's', 'Ŝ': 'S', 'ŝ': 's', 'Ş': 'S', 'ş': 's', 'Š': 'S', 'š': 's', 'Ţ': 'T', 'ţ': 't', 'Ť': 'T', 'ť': 't', 'Ŧ': 'T', 'ŧ': 't', 'Ũ': 'U', 'ũ': 'u', 'Ū': 'U', 'ū': 'u', 'Ŭ': 'U', 'ŭ': 'u', 'Ů': 'U', 'ů': 'u', 'Ű': 'U', 'ű': 'u', 'Ų': 'U', 'ų': 'u', 'Ŵ': 'W', 'ŵ': 'w', 'Ŷ': 'Y', 'ŷ': 'y', 'Ÿ': 'Y', 'Ź': 'Z', 'ź': 'z', 'Ż': 'Z', 'ż': 'z', 'Ž': 'Z', 'ž': 'z', 'ſ': 's', 'ƒ': 'f', 'Ơ': 'O', 'ơ': 'o', 'Ư': 'U', 'ư': 'u', 'Ǎ': 'A', 'ǎ': 'a', 'Ǐ': 'I', 'ǐ': 'i', 'Ǒ': 'O', 'ǒ': 'o', 'Ǔ': 'U', 'ǔ': 'u', 'Ǖ': 'U', 'ǖ': 'u', 'Ǘ': 'U', 'ǘ': 'u', 'Ǚ': 'U', 'ǚ': 'u', 'Ǜ': 'U', 'ǜ': 'u', 'Ǻ': 'A', 'ǻ': 'a', 'Ǽ': 'AE', 'ǽ': 'ae', 'Ǿ': 'O', 'ǿ': 'o'};
                    var valueResult = '';
                    for (var i = 0; i < srt.length; i++) {
                        var c = srt.charAt(i);
                        valueResult += map[c] || c;
                    }
                    return valueResult;
                },
                removeFilterFromList: function(slug) {
                    $.each(filtersData, function(idx_group, group ){
                        $.each(group.filters, function(idx_filter, filter) {
                            if(typeof(filter) !== 'undefined' && filter.slug === slug){
                                filtersData[idx_group].filters[idx_filter].shortcut = 'hidden';
                            }
                        });
                    });
                },
                recoverTopics: function(f) {
                    // clean suggestion div
                    $suggestions.empty();
                    var self = this;
                    $.each(filtersData, function(index, group){
                        var title = $('<strong>').text(group.name);
                        var groupSlug = group.slug;
                        var $ul = $('<ul></ul>');
                        var show = false;
                        $.each(group.filters, function(index, filter){
                            var slugNorm = (filter.shortcut || filter.slug).toLowerCase();
                            var nameNorm = self.removeAccents(filter.name.toLowerCase());
                            if ((!f || slugNorm.indexOf(self.removeAccents(f.toLowerCase())) != -1 || nameNorm.indexOf(self.removeAccents(f.toLowerCase())) != -1) && filter.shortcut != 'hidden') {
                                var $li = $('<li></li>')
                                    .attr('data-slug', filter.slug)
                                    .addClass('sug');
                                var $a = $('<a></a>')
                                    .attr('class', 'search-ss')
                                    .attr('href', '#')
                                    .html(filter.name + ' <span>#' + (filter.shortcut || filter.slug) + '</span>')
                                    .appendTo($li)
                                    .on('click', function(e){
                                        e.preventDefault();
                                        self.addFilter(filter.slug, groupSlug, filter.shortcut);
                                        $searchInput.val($searchInput.val().replace('#'+f, ''));
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
                        if(show){
                            $suggestions.append(title);
                            $suggestions.append($ul);
                        }
                    });
                }
            };

            // prepare input
            fnSuggestions.prepareInput();

            // load previouly selected filters
            if(settings.filters){
                $.each(settings.filters, function(sidx, sfilter){

                    // foreach filters to get the correct shortcut
                    $.each(filtersData, function(index, group){
                        if(group.slug === sfilter.group){
                            $.each(group.filters, function(index, filter){
                                if(typeof(filter) !== 'undefined' && filter.slug === sfilter.slug) {
                                    fnSuggestions.addFilter(sfilter.slug, sfilter.group, filter.shortcut);
                                    fnSuggestions.removeFilterFromList(sfilter.slug);
                                }
                            });
                        }
                    });
                });
                $searchInput.focus();
            }

            // events
            $searchForm.on('click', function() {
                $searchInput.focus();
            });


            $searchInput.on('input', function(e){

                fnSuggestions.storeSize();
                fnSuggestions.parseAndAddFilters();

                // find out if there is a difference of exactly one # between input.value and previousValue
                // Current algorithm is very simple. Must be improved in the future
                // Currently consider only the last character
                if($searchInput.val().length - previousValue.length === 1 &&
                   $searchInput.val()[$searchInput.val().length -1] === '#') {
                    fnSuggestions.open();
                }
                else if(previousValue.length - $searchInput.val().length === 1 &&
                        previousValue[previousValue.length -1] === '#') {
                    fnSuggestions.close();
                }

                fnSuggestions.populate();

                previousValue = $searchInput.val();
            });

            $showTopics.on('click', function(e){
                e.preventDefault();
                if($suggestions.attr('data-hidden') == 'false') {
                    fnSuggestions.close();
                }else{
                    fnSuggestions.open();
                    fnSuggestions.populate();
                }
            })

            $rightColumFilters.on('change', function() {
                var rslug = $(this).val();
                var rgroup = $(this).attr('name');
                var rshortcut = '';
                if($(this).is(':checked')) {
                    // Need to foreacht to recover the filter shortcut
                    $.each(filtersData, function(idx_group, group){
                        $.each(group.filters, function(idx_filter, filter){
                            if(typeof(filter) !== 'undefined' && filter.slug === rslug){
                                rshortcut = filter.shortcut;
                            }
                        });
                    });

                    fnSuggestions.addFilter(rslug, rgroup, rshortcut);
                    fnSuggestions.removeFilterFromList(rslug);
                } else {
                    $searchFilters.find('[data-topic="'+rslug+'"]').remove();
                }

            });

            $form.on('submit', function(e){
                e.preventDefault();

                var topics = $.makeArray($form.find('.topic')).map(function(e){
                    var topic = { 'filter': $(e).data('topic'), 'group': $(e).data('group') };
                    return topic;
                });
                var topicsString = topics.map(function(t){
                    return t.group + '=' + t.filter;
                }).join('&');
                var searchQuery = encodeURIComponent($searchInput.val());

                // Redirects to search
                location.href = BASE_SEARCH_URL + '?' + 'q=' + searchQuery + (topicsString ? '&' + topicsString : '');
            });

        });
    };

})(window, document, jQuery);
