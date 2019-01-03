(function(doc, win, $) {
    'use strict';

    /**
     * Handles setting up and binding events for tooltips.
     * Currently this tooltip is only used by the payments form.
     * The SCSS for this is located at:
     * kuma/static/styles/components/payments/_tooltip.scss
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
            $(tooltip)
                .addClass('is-open')
                .attr('aria-hidden', false);

            $(doc).on('click.tooltipHandler', function(event) {
                if (
                    !$(tooltip)
                        .get(0)
                        .contains(event.target) ||
                    $(event.target).hasClass('tooltip-close')
                ) {
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
                label: 'Tooltip Opened'
            });
        }

        /**
         * Hides the tooltip and sets the relevant element properties.
         * @param {Element} tooltip Tooltip element to hide.
         */
        function closeTooltip(tooltip) {
            $(tooltip)
                .removeClass('is-open')
                .attr('aria-hidden', true);

            $(doc).off('click.tooltipHandler');
            $(win).off('resize.tooltipHandler');

            // Send GA Event.
            mdn.analytics.trackEvent({
                category: 'payments',
                action: 'banner',
                label: 'Tooltip Closed'
            });
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

            if (tooltip.classList.contains('is-open')) {
                closeTooltip(tooltip);
            } else {
                openTooltip(tooltip);
            }
        });
    }

    setupTooltips();
})(document, window, jQuery);
