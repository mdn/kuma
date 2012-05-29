/*
	Customizations to jQuery UI's autocomplete widget for better use in
	"locking in" a value
*/
(function() {
	
    // Create our own widget
    $.widget("ui.mozillaAutocomplete", $.ui.autocomplete, {
		
		/* Additional options */
		// If we want to require a value be chosen, we should 
		options: {
			requireValidOption: false,
			onSelect: function(selectionObj, isSilent){},
			onDeselect: function(oldSelection){},
			autocompleteURL: "",
			styleElement: null
		},
		
		// Create a cache - make this a 
		cache: null,
		
		// Selection - the last selected item
		selection: null,
		
		// Store the last XHR
		lastXHR: null,
		
		updateStyles: function(valid) {
			var validClass = "ui-autocomplete-input-valid",
				invalidClass = "ui-autocomplete-input-invalid";
			
			if(valid == "all") {
				this.styleElement.removeClass(validClass).removeClass(invalidClass);
			}
			else if(valid) {
				this.styleElement.addClass(validClass).removeClass(invalidClass);
			}
			else {
				this.styleElement.removeClass(validClass).addClass(invalidClass);
			}
		},
		
		// Modify the suggest method to show only if the element is focused
		_suggest: function(items) {
			if(this.isFocused) {
				$.ui.autocomplete.prototype._suggest.call(this, items);
			}
		},
		
		// Deselecter
		deselect: function(fireCallback) {
			var oldSelection = this.selection;
			
			this.clear();
			
			if(this.element.val() && this.options.requireValidOption) {
				this.updateStyles(false);
			}
			
			// Fire callback
			this.options.onDeselect(oldSelection);
		},
		
		clear: function() {
			this.selection = null;
			
			// Set the title attribute
			this.element.attr("title", gettext("No selection"));
			
			// Remove the valid and invalid classes
			this.updateStyles("all");
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
			
			
			var oldSource = this.source;
			this.source = function(request, response) {
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
				};
				
				// Search the cache for the results first;  if found, return it
				if(cache.terms[term]) {
					response(cache.terms[term]);
					return;
				}
				
				// Trigger a new AJAX request to find the results
				self.lastXHR = $.getJSON(self.options.autocompleteUrl, request, function(data, status, xhr) {
					// Cache results
					$.each(data, function() {
						cache.keys[this.label.toLowerCase()] = this;
					});
					cache.terms[term] = data;
					
					// Respond with data *if* this is the last request
					if(xhr == self.lastXHR) {
						response(data);
					}
				});
			};
			
			// Modify selection
			var select = this.options.select;
			this.options.select = function(event, ui, isSilent) {
				// Set the selection
				var selection = self.selection = ui.item;
				// Call the select method if present
				if(select) select.call(self, event, ui);
				// Set the INPUT element's value to the item value
				self.element.val(selection.value);
				// Add the valid class
				self.updateStyles(true);
				// Set the title attribute
				self.element.attr("title", gettext("Selected: ") + self.selection.label);
				// Call onSelect for callback purposes
				self.options.onSelect(selection, isSilent);
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
				if(e && e.keyCode == 13) {
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
		}
    });
	
})();