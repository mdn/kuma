(function(doc, win, $) {
    'use strict';

    /**
     * Handles setting up and binding events for tooltips.
     */
    function setupTooltips() {
        var buttons = $('.tooltip-button');

        if (!buttons.length) {
            return;
        }

        /**
         * Shows the tooltip and sets the relevant element properties.
         * @param {Element} tooltip Tooltip element to show.
         */
        function openTooltip(tooltip) {
            // Moves tooltip to the end of the body so we can position correctly.
            tooltip.appendTo('body');
            tooltip.addClass('is-open')
                .attr('aria-hidden', false);

            $(doc).on('click.tooltipHandler', function(event) {
                if (!tooltip.get(0).contains(event.target) || $(event.target).hasClass('tooltip-close')) {
                    event.preventDefault();

                    closeTooltip(tooltip);
                }
            });

            $(win).on('resize.tooltipHandler', function() {
                closeTooltip(tooltip);
            });

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'Tooltip Opened',
            });
        }

        /**
         * Hides the tooltip and sets the relevant element properties.
         * @param {Element} tooltip Tooltip element to hide.
         */
        function closeTooltip(tooltip) {
            tooltip.removeClass('is-open has-arrow-top')
                .attr('aria-hidden', true)
                .css({
                    left: 0,
                    top: 0
                });

            $(doc).off('click.tooltipHandler');
            $(win).off('resize.tooltipHandler');

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'Tooltip Closed',
            });
        }

        /**
         * Positioning the tooltip to the left or below the button depending on the available space.
         * @param {Element} tooltip Tooltip element.
         * @param {Element} element Tooltip button element.
         */
        function positionTooltip(tooltip, element) {
            // Is opening is added to remove display: none, but still keep the tooltip hidden
            // so we can get its dimensions and positino without showing it.
            tooltip.addClass('is-opening');

            var tooltipDomRect = tooltip.get(0).getBoundingClientRect();
            var elementDomRect = element.get(0).getBoundingClientRect();
            var position;

            // Checks for available width to the left of the button and positions the tooltip below the button if none
            // there isn't enough.
            if (tooltipDomRect.width > elementDomRect.left) {
                position = {
                    left: elementDomRect.left + elementDomRect.width - tooltipDomRect.width + 4,
                    top: elementDomRect.top + elementDomRect.height + win.scrollY + 10
                };

                tooltip.addClass('has-arrow-top');
            } else {
                position = {
                    left: elementDomRect.left - (elementDomRect.width / 2) - (tooltipDomRect.width - 10),
                    top: elementDomRect.top + (elementDomRect.height / 2) - (tooltipDomRect.height / 2) + win.scrollY
                };
            }

            $(tooltip).css(position);

            // Switch back to display: none; which will be removed when openTooltip() is called.
            tooltip.removeClass('is-opening');
        }

        // Handle clicks to the tooltip button.
        buttons.on('click', function(event) {
            event.stopImmediatePropagation();
            event.preventDefault();

            var target = $(event.target).closest('[aria-controls]');

            if (!target.length) {
                return;
            }

            var tooltipId = target.get(0).getAttribute('aria-controls');
            var tooltip = doc.getElementById(tooltipId);

            if (!tooltip) {
                return;
            }

            tooltip = $(tooltip);

            if (tooltip.hasClass('is-open')) {
                closeTooltip(tooltip);
            } else {
                positionTooltip(tooltip, target);
                openTooltip(tooltip);
            }
        });
    }

    setupTooltips();
})(document, window, jQuery);