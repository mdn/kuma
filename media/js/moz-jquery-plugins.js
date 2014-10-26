/*
    Customizations to jQuery UI's autocomplete widget for better use in
    'locking in' a value
*/
(function($) {
    'use strict';

    // Move the suggestion list when the page scrolls and the list is open
    function openCloseScroll(event) {
        return function() {
            var self = this;
            $(window)[event]('scroll', function() {
                $(self).mozillaAutocomplete('reposition');
            });
        };
    }

    /*
        Customized autocomplete that provides:
            *  Cache management
            *  Additional callbacks
            *  Color based success/failure selections
            *  more....
    */
    $.widget('ui.mozillaAutocomplete', $.ui.autocomplete, {

        /* Additional options */
        options: {
            // Shows an 'invalid' style if something good isn't picked
            requireValidOption: false,
            // Callback for selection;  true selection or 'silent' selection
            onSelect: function(selectionObj, isSilent){},
            // Callback for when a selection is deselected via this plugin
            onDeselect: function(oldSelection){},
            // URL to hit to retrieve results
            autocompleteURL: '',
            // Element to style and add 'valid' and 'invalid' classes to
            styleElement: null,
            // Minimum length of search before XHR is fired
            minLength: 3,
            // Method that can modify the request / data object
            buildRequestData: function(req) {
                return req;
            },
            // The data object property which will also be the label
            labelField: 'title',
            // Allow overriding of '_renderItem' method
            _renderItem: null,
            // Show items as anchors with title attributes
            _renderItemAsLink: false,
            open: openCloseScroll('bind'),
            close: openCloseScroll('unbind')
        },

        // Create a cache - make this a
        cache: null,

        // Selection - the last selected item
        selection: null,

        // Store the last XHR
        lastXHR: null,

        // Updates the styleElement (usually the INPUT)'s CSS styles
        updateStyles: function(valid) {
            var validClass = 'ui-autocomplete-input-valid',
                invalidClass = 'ui-autocomplete-input-invalid',
                styleElement = this.styleElement;

            if(valid === 'all') {
                styleElement.removeClass(validClass).removeClass(invalidClass);
            }
            else if(valid) {
                styleElement.addClass(validClass).removeClass(invalidClass);
            }
            else {
                styleElement.removeClass(validClass).addClass(invalidClass);
            }
        },

        // Modify the suggest method to show only if the element is focused
        _suggest: function(items) {
            if(this.isFocused) {
                $.ui.autocomplete.prototype._suggest.call(this, items);
            }
        },

        // Deselection a current selection if exists
        deselect: function() {
            var oldSelection = this.selection;

            this.clear();

            if(this.element.val() && this.options.requireValidOption) {
                this.updateStyles(false);
            }

            // Fire callback
            this.options.onDeselect(oldSelection);
        },

        // Clears the stored selection and updates styling
        clear: function() {
            this.selection = null;

            // Set the title attribute
            this.element.attr('title', gettext('No selection'));

            // Remove the valid and invalid classes
            this.updateStyles('all');
        },

        // Override _create for our purposes
        _create: function() {

            var self = this;
            $.ui.autocomplete.prototype._create.call(this);

            // Create the cache
            if(!this.cache) var cache = this.cache = {
                terms: {},
                keys: {}
            };

            // Keep focus state
            this.isFocused = false;
            this.element.focus(function() {
                self.isFocused = true;
            });
            this.element.blur(function() {
                self.isFocused = false;
                var value = self.element.val();

                // If there's no selection, a value, and no lookup for what is there...
                if(value && !this.selection && !cache.keys[value.toLowerCase()]) {
                    self._search(value);
                }
            });

            // Decide which element gets styles!
            this.styleElement = $(this.options.styleElement || this.element);

            // Set the 'source' method -- the one that executes searches or returns the filtered static array
            var oldSource = this.source;
            this.source = $.isArray(this.options.source) ?
                function(request, response) {
                    assignLabel(self.options.source);
                    response($.ui.autocomplete.filter(self.options.source, request.term));
                } :
                function(request, response) {
                    // Format the request
                    request = this.options.buildRequestData(request);

                    // Put the term in lowercase for caching purposes
                    var term = request.term.toLowerCase();

                    // Modify the response;  if there are matches and they've blurred, pick the first
                    var originalResponse = response;
                    response = function(data) {
                        originalResponse.call(self, data);

                        if(data.length && cache.keys[term]) {
                            // Set the selection
                            self.options.select.call(self, null, { item: cache.keys[term] }, true);
                        }
                        else {
                            // If no data, we know it's not good
                            self.deselect();
                        }
                    };

                    // Search the cache for the results first;  if found, return it
                    if(cache.terms[term]) {
                        response(cache.terms[term]);
                        return;
                    }

                    // Trigger a new AJAX request to find the results
                    self.lastXHR = $.getJSON(self.options.autocompleteUrl, request, function(data, status, xhr) {
                        // Message the data
                        assignLabel(data);

                        // Cache results
                        $.each(data, function() {
                            cache.keys[this.label.toLowerCase()] = this;
                        });
                        cache.terms[term] = data;

                        // Respond with data *if* this is the last request
                        if(xhr === self.lastXHR) {
                            response(data);
                        }
                    });
                };

            // Modify selection
            var select = this.options.select;
            this.options.select = function(event, ui, isSilent) {
                // Set the selection
                var selection = self.selection = ui.item;
                if(selection.value !== undefined) {
                        // Call the select method if present
                    if(select) select.call(self, event, ui);
                    // Set the INPUT element's value to the item value
                    if(selection) self.element.val(selection.value);
                    // Add the valid class
                    self.updateStyles(true);
                    // Set the title attribute
                    self.element.attr('title', gettext('Selected: ') + self.selection.label);
                    // Call onSelect for callback purposes
                    self.options.onSelect(selection, isSilent);
                }
            };

            // Add keyup event so that if they don't select from the
            // dropdown, but pick something valid, set that
            this.element.keyup(function(e) {

                var term = self.element.val().toLowerCase(),
                    lookup = cache.keys[term];

                // Set selection if present
                if(lookup) {
                    self.selection = self.cache.keys[term];
                }
                else {
                    self.deselect();
                }

                // Stop ENTER key presses from submitting forms...
                if(e && e.keyCode === 13) {
                    e.preventDefault();
                    e.stopPropagation();
                    if(lookup) {
                        self.options.select.call(self, e, { item: self.selection });
                    }

                    return;
                }

                if(lookup) {
                    // Add the valid class
                    self.updateStyles(true);
                    // Set the selection
                    self.options.onSelect(self.selection, true);
                }
            });

            // If there's an initial value and we must match, we need search initially
            if(self.options.requireValidOption && self.element.val()) {
                self.search(self.element.val());
            }

            // Utility function to message data before any of it is displayed to the user
            function assignLabel(data) {
                $.each(data, function() {
                    this.label = this[self.options.labelField];
                });
                return data;
            }

            // If the user wants to override the '_renderItem' method, let them
            if(self.options._renderItem) {
                self._renderItem = self.options._renderItem;
            }
            else if(self.options._renderItemAsLink) {
                self._renderItem = function(list, item) {
                    return $('<li></li>')
                            .data('item.autocomplete', item)
                            .attr('title', item.url)
                            .append($('<a></a>').text(item.label))
                            .appendTo(list);
                };
            }
        },

        reposition: function() {
            this.menu.element.position( $.extend({
                of: this.element
            }, this.options.position ));
        }
    });

    /*
        Plugin that adds placeholder text to the INPUTs on focus/blur
    */
    $.fn.mozPlaceholder = function() {
        return this.each(function() {
            var $input = $(this);
            var placeholder = $input.attr('placeholder');

            var valCheck = function() {
                var box = $input[0];
                if(box.value === placeholder) {
                     box.value = '';
                }
            };

            // Events
            valCheck();
            $input.bind({
                blur: valCheck,
                focus: function() {
                    if($input.val() === '') {
                        $input.val(placeholder);
                    }
                }
            });
        });
    };

})(jQuery);
