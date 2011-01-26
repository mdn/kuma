/**
 * JavaScript library written for Kitsune by Mozilla.
 * License: MPL
 * License URL: http://www.mozilla.org/MPL/
 *
 * Contains a jQuery function that takes an element and adds makes it open
 * a modal window on click.
 */


/*
 * Initialize modals that activate on the click of elements with
 * class="activates-modal". The activation element is required to
 * have a data-modal-selector attribute that is a CSS selector
 * to the modal to activate (by adding CSS class "active").
 *
 * Options:
 *     * modal: the modal window it targets.
 *     * overlay_close: close when overlay is clicked, default false
 *     * escape_close: close when hitting escape, default false
 */
jQuery(document).ready(function() {

k.open_modal = $();  // keeps track of open modals, since escape_close needs it
jQuery.fn.initClickModal = function (options) {
    // Make it work on an array of elements too
    if (this.length > 1) {
        this.each(function() {
            $(this).initClickModal();
        });
        return this;
    }

    var $this = this, $overlay;

    options = $.extend({
        modal: $($this.attr('data-modal-selector')),
        overlay_close: false,
        escape_close: false
    }, options);

    function closeModal(ev, $modal) {
        ev.preventDefault();
        k.open_modal.removeClass('active');
        $('#modal-overlay').remove();
    }

    $this.click(function(ev) {
        ev.preventDefault();
        if (!options.modal.data('inited')) {
            options.modal.append('<a href="#close" class="close">&#x2716;</a>')
                .data('inited', true);
            options.modal.delegate('a.close, a.cancel, input[name="cancel"]',
                                   'click', closeModal);
        }

        options.modal.addClass('active');
        k.open_modal = options.modal;

        if ($('#modal-overlay').length === 0) {
            $overlay = $('<div id="modal-overlay"></div>');
            $('body').append($overlay);
            if (options.overlay_close) {
                $overlay.click(closeModal);
            }
        }

        return false;
    });

    if (options.escape_close && !$('body').data('close-modal')) {
        $('body').keypress(function(ev) {
            if ($('#modal-overlay:visible').length !== 0 &&
                ev.keyCode === 27) {  // escape key was pressed
                closeModal(ev);
            }
        });
        $('body').data('close-modal', true);
    }

    return this;
};

});
