/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/**
 * A KBox type and a corresponding jQuery plugin.
 *
 * So, what is a kbox?
 * A kbox can be a modal dialog or a (dhtml, not window) popup or a ...
 * The kbox can be configured programatically or using data-* attributes.
 * Default styles are in kbox.css.
 *
 * Usage
 *      Declarative:
 *      <a id="example-id" ...>Click here to show modal</a>
 *      <div class="kbox" title="A modal dialog" data-target="#example-id" data-modal="true">
 *          .... modal content ....
 *      </div>
 *
 *      Programatic:
 *      var kbox = new KBox('<p>Some content</p>', {
 *          title: 'KBox Title'
 *      });
 *      kbox.open();
 *
 *      Mixed:
 *      [HTML]
 *      <a id="a-id" ...>Click ...</a>
 *      <div id="kbox-id" class="kbox" data-target="a-id">...content...</div>
 *      [JavaScript]
 *      var kbox = $('kbox-id').data('kbox'); // Gets the kbox instance.
 *      kbox.updateOptions({
 *          preOpen: function() {
 *              // If isFormValid() returns false, the kbox doesn't open;
 *              return isFormValid();
 *          }
 *      });
 *
 * Options
 *      clickTarget / data-target:
 *          jQuery or DOM elements or CSS Selector to target(s)
 *          that will trigger the kbox to open on click. Optional.
 *      closeOnEsc / data-close-on-esc:
 *          Close the kbox on ESC. Default: true.
 *      closeOnOutClick: / data-close-on-out-click:
 *          Close the kbox on any click outside of it. Default: false.
 *      container / data-container:
 *          jQuery or DOM element for appending the kbox. Optional.
 *          If html string is passed as the content of the kbox, container
 *          will default to $('body').
 *      destroy / data-destroy:
 *          Clean up DOM changes on close. Default: false.
 *      id / data-id:
 *          An id for the kbox container. Optional.
 *      modal / data-modal:
 *          Do we need to make the kbox modal? Adds a background overlay.
 *          Default: false.
 *      position / data-position:
 *          Where to position the kbox.
 *              'center': (default) centers the kbox in the window
 *              'none': doesn't do any positioning so you can do it in CSS
 *              (TODO:) 'force-center': keeps kbox center as window scrolls
 *      preOpen:
 *          A function to call before opening the kbox. If the function
 *          returns false, the kbox isn't opened. Optional.
 *      template:
 *          Override the template to use for creating the modal.
 *      title:
 *          The kbox's title.
 */

(function($) {

"use strict"; // Giving this a shot!

var TEMPLATE =
    '<div class="kbox-container">' +
      '<a href="#close" class="kbox-close">&#x2716;</a>' +
      '<div class="kbox-title"></div>' +
      '<div class="kbox-wrap"><div class="kbox-placeholder"/></div>' +
    '</div>',
    OVERLAY =
    '<div id="kbox-overlay"></div>';

// The KBox type
function KBox(el, options) {
    KBox.prototype.init.call(this, el, options);
}

KBox.prototype = {
    init: function(el, options) {
        var self = this;
        self.el = el;
        self.html = typeof el === 'string' && el;
        self.$el = $(el);
        options = $.extend({
            // defaults
            clickTarget: self.$el.data('target'),
            closeOnEsc: self.$el.data('close-on-esc') === undefined ?
                            true : !!self.$el.data('close-on-esc'),
            closeOnOutClick: !!self.$el.data('close-on-out-click'),
            container: self.html && $('body'),
            // TODO: maxHeight: self.$el.data('max-height') || 'window',
            destroy: !!self.$el.data('destroy'),
            id: self.$el.data('id'),
            modal: !!self.$el.data('modal'),
            position: self.$el.data('position') || 'center',
            preOpen: false,
            template: TEMPLATE,
            title: self.$el.attr('title')
        }, options);
        self.options = options;
        self.$clickTarget = options.clickTarget && $(options.clickTarget);
        self.$container = options.container && $(options.container);
        self.rendered = false; // did we render out yet?
        self.$ph = false; // placeholder used if we need to move self.$el in the DOM.
        self.$kbox = $();

        // Make the instance accessible from the DOM element.
        self.$el.data('kbox', self)

        // If we have a click target, open the kbox when it is clicked.
        if (self.$clickTarget) {
            self.$clickTarget.click(function(ev) {
                ev.preventDefault();
                self.open();
            });
        }

    },
    updateOptions: function(options) {
        // Ability to update options programmatically after kbox creation.
        var self = this;
        self.options = $.extend(self.options, options);
        self.$clickTarget = options.clickTarget && $(options.clickTarget);
        self.$container = options.container && $(options.container);
    },
    render: function() {
        var self = this;
        self.$kbox = $(self.options.template);

        if (self.$container) {
            // The kbox will be appended to the container.
            if (self.$el.parent().length) {
                // If we are attached to the DOM, save our place there
                // for putting everything back in place later.
                self.$ph = self.$el.before('<div style="display:none;"/>').prev();
            }
            self.$kbox.appendTo(self.$container);
        } else {
            // The kbox will go right where $el is.
            self.$el.before(self.$kbox);
        }

        // Set the id if it was specified
        self.options.id && self.$kbox.attr('id', self.options.id);

        // Set the title if it was specified.
        self.options.title && self.$kbox.find('.kbox-title').text(self.options.title);

        // Insert the content.
        self.$kbox.find('.kbox-placeholder').replaceWith(self.$el.detach());

        // Handle close events
        self.$kbox.delegate('.kbox-close, .kbox-cancel', 'click', function(ev) {
            ev.preventDefault();
            self.close();
        });

        self.rendered = true;
    },
    open: function() {
        var self = this;
        if (self.options.preOpen && !self.options.preOpen.call(self)) {
            // If we have a preOpen callback and it returns false,
            // we don't open anything.
            return;
        }
        self.rendered || self.render();
        self.$kbox.addClass('kbox-open');
        self.setPosition();
        self.options.modal && self.createOverlay();

        // Handle ESC
        if (self.options.closeOnEsc) {
            self.keypressHandler = function(ev) {
                if(ev.keyCode === 27) {
                    self.close();
                }
            };
            $(document).keypress(self.keypressHandler);
        }

        // Handle outside clicks
        if (self.options.closeOnOutClick) {
            self.clickHandler = function(ev) {
                if ($(ev.target).closest('.kbox-container').length === 0) {
                    // The click isn't inside the kbox, so lets close it.
                    self.close();
                }
            };
            setTimeout(function() { // so it doesn't get triggered on this click
                $('body').click(self.clickHandler);
            }, 0);
        }
    },
    setPosition: function(position) {
        var self = this,
            toX, toY, $parent, parentOffset, minX, minY, scrollL, scrollT;
        if (!position) {
            position = self.options.position;
        }
        if (position === 'none' || !self.$kbox.length) {
            return;
        }
        if (position === 'center') {
            $parent = self.$kbox.offsetParent();
            parentOffset = $parent.offset();
            scrollL = $(window).scrollLeft();
            scrollT = $(window).scrollTop();
            minX = -parentOffset.left + scrollL;
            minY = -parentOffset.top + scrollT;
            toX = ($(window).width()
                  - self.$kbox.outerWidth()) / 2
                  - parentOffset.left
                  + scrollL;
            toY = ($(window).height()
                  - self.$kbox.outerHeight()) / 2
                  - parentOffset.top
                  + scrollT;
            if (toX < minX) {
                toX = minX;
            }
            if (toY < minY) {
                toY = minY;
            }
            self.$kbox.css({
                'left': toX,
                'top': toY,
                'right': 'inherit',
                'bottom': 'inherit'
            });
        }
    },
    close: function() {
        var self = this;
        self.$kbox.removeClass('kbox-open');
        self.options.modal && self.destroyOverlay();
        self.options.destroy && self.destroy();
        if (self.options.closeOnEsc) {
            $('body').unbind('keypress', self.keypressHandler);
        }
        if (self.options.closeOnOutClick) {
            $('body').unbind('click', self.clickHandler);
        }
    },
    destroy: function() {
        // return DOM to how it was originally, if possible.
        var self = this;
        if (self.$container && self.$ph) {
            self.$ph.replaceWith(self.$el.detach());
        }
        self.$kbox.remove();
    },
    createOverlay: function() {
        var self = this;
        self.$overlay = $(OVERLAY);
        self.$kbox.before(self.$overlay);
    },
    destroyOverlay: function() {
        if (this.$overlay) {
            this.$overlay.remove();
            delete this.$overlay;
        }
    }
};

// Create the jQuery plugin.
$.fn.kbox = function(options) {
    return this.each(function() {
        new KBox(this, options);
    });
};

// Expose KBox to the world, in case they don't want to use the plugin.
window.KBox = KBox;

// Initialize declared kboxes.
$('.kbox').kbox();

})(jQuery);
