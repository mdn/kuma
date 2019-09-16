(function(win, doc, $) {
    'use strict';

    // Private var to assign IDs to history for accessibility purposes
    var historyCount = 0;

    // The open button template
    var $historyLink = $('<button title="' + gettext('Open implementation notes') + '" class="bc-history-link only-icon" tabindex="-1"><span>' + gettext('Open') + '</span><i class="ic-history" aria-hidden="true"></i></button>');
    var historyCloseButtonIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="28" viewBox="0 0 22 28"><path d="M20.281 20.656c0 .391-.156.781-.438 1.062l-2.125 2.125c-.281.281-.672.438-1.062.438s-.781-.156-1.062-.438L11 19.249l-4.594 4.594c-.281.281-.672.438-1.062.438s-.781-.156-1.062-.438l-2.125-2.125c-.281-.281-.438-.672-.438-1.062s.156-.781.438-1.062L6.751 15l-4.594-4.594c-.281-.281-.438-.672-.438-1.062s.156-.781.438-1.062l2.125-2.125c.281-.281.672-.438 1.062-.438s.781.156 1.062.438L11 10.751l4.594-4.594c.281-.281.672-.438 1.062-.438s.781.156 1.062.438l2.125 2.125c.281.281.438.672.438 1.062s-.156.781-.438 1.062L15.249 15l4.594 4.594c.281.281.438.672.438 1.062z"/></svg>';
    // The close button template
    var $historyCloseButton = $('<button class="bc-history-button only-icon"><abbr title="' + gettext('Return to compatibility table.') + '"><span>' + gettext('Close') + '</span>' + historyCloseButtonIcon + '</abbr></button>');

    var animationProps = {
        duration: 150,
        queue: false,
        easing: 'linear'
    };

    //  Usage: $('.compat-table').mozCompatTable();
    return jQuery.fn.mozCompatTable = function() {

        return $(this).each(function() {

            var $table = $(this);

            // Keep track of what may be open within this table
            var $openCell;

            // This limits very quick opening and closing of cells which results in incorrect height counts
            var animating = false;

            var subjectAnimation = $.extend({ complete: function() { animating = false; } }, animationProps);

            // Activate all history cells for keyboard
            $table.find('.bc-has-history').each(function() {
                var historyId = 'bc-history-' + (++historyCount);
                var $td = $(this);
                var $history = $td.find('.bc-history');

                $td.attr({
                    tabIndex: 0,
                    'aria-expanded': false,
                    'aria-controls': historyId
                });

                $history.attr('id', historyId);
                // generate and add button to open history tray
                $historyLink.clone().insertBefore($history);
            });

            // Listen for interaction on "history" cells
            $table.on('click touchend', '.bc-has-history', function(e) {
                var $actualTarget = $(e.target);

                // Don't open/close if the user interaction is within the history section
                if ($actualTarget.parents('.bc-history').length || $actualTarget.hasClass('bc-history')) {
                    e.stopImmediatePropagation();
                    return;
                }

                // prevent touch event from bubbling to a click event as well
                // has no effect if this was a click
                e.preventDefault();

                // Close previous cell, open the next one
                closeAndOpenHistory($(this));
            });

            // Listen for interaction on "close" buttons
            $table.on('click touchend', '.bc-history-button', function(ev) {
                ev.stopImmediatePropagation();
                hideHistory();
            });

            // Listen for keyboard events to open/close history
            $table.on('keypress', '.bc-has-history', function(ev) {
                var $td = $(this);
                var key = ev.which;

                if (key === 13 || key === 32) {
                    closeAndOpenHistory($td);
                    ev.preventDefault();
                } else if (key === 27) {
                    hideHistory();
                    ev.preventDefault();
                }
            });

            /** Function which closes any open history items, then opens the target history item
                Acts as the "router" for open and close directives */
            function closeAndOpenHistory($td) {
                if (animating) {
                    return;
                }

                // If no cell is open at the moment, skip the "close" step and just open it
                if (!$openCell) {
                    return _open($td);
                }

                // If click event is from the currently closing cell, set $td to null
                var previousOpenCell = $openCell && $openCell.get(0);
                if ($td.get(0) === previousOpenCell) {
                    $td = null;
                }

                // Close what's open, if anything, and open if $td has a value
                hideHistory($td);
            }

            /** Opens the history for a given item */
            function showHistory() {
                if (animating) {
                    return;
                }

                var $row = $openCell.closest('tr');
                var $history = $openCell.find('.bc-history').outerWidth($table.width());

                // get cell coords
                var cellLeft = $openCell.offset().left;

                // get cell border widths
                var cellBorders = $openCell.css(['border-top-width', 'border-left-width', 'border-bottom-width']);

                // get table coords
                var tableLeft = $table.offset().left;

                // left coord of table minus left coord of cell
                var historyLeft = tableLeft - cellLeft - parseInt(cellBorders['border-left-width'], 10);

                // get cell height
                var cellTop = $openCell.outerHeight();

                var historyTop = cellTop - parseInt(cellBorders['border-bottom-width'], 10) - parseInt(cellBorders['border-top-width'], 10);

                var historyHeight;
                var $subject;
                var displayDetect;

                // Add a close button if one doesn't already exist
                if ($history.find('.bc-history-button').length === 0) {
                    $historyCloseButton.clone().appendTo($history);
                }

                // move history where it will display
                $history.css({ left: historyLeft, top: historyTop });

                // measure height
                $history.css('display', 'block').attr('aria-hidden', false);
                historyHeight = $history.outerHeight();

                // set max-height to 0 and visibility to visible
                $openCell.addClass('active').attr('aria-expanded', true);

                // add measured height to history and to the cell/row it is being displayed beneath (CSS handles transition)
                displayDetect = parseInt($table.find('thead td').first().css('z-index'));

                if (displayDetect === 1 ) {
                    $subject = $row.find('td');
                } else if (displayDetect === 2) {
                    $subject = $openCell;
                } else {
                    $subject = $row.find('th, td');
                }

                animating = true;
                $history.css('height', 0).stop().animate({ height: historyHeight }, animationProps);

                $subject.stop().animate({ borderBottomWidth: historyHeight }, subjectAnimation);
            }

            /**
             * Hides the history dropdown for a given cell
             * @param {Object} [$td] - Hides the dropdown for this cell
             */
            function hideHistory($td) {
                var $history;

                if (animating) {
                    return;
                }

                // Animate the borders back down
                $openCell.attr('aria-expanded', false).stop().animate({ borderBottomWidth: '' }, animationProps);
                $openCell.closest('tr').find('th, td').stop().animate({ borderBottomWidth: '' }, animationProps);

                $history = $openCell.find('.bc-history');

                var historyAnimationProps = $.extend({
                    complete: function() {
                        $openCell.removeClass('active');
                        $history.css('display', 'none').css('height', 'auto');
                        $openCell = null;

                        if ($td) {
                            _open($td);
                        }
                    }
                }, animationProps);

                $history.attr('aria-hidden', true).stop().animate({ height: '' }, historyAnimationProps);

                // if the focus is inside the .bc-history and we'd lose our keyboard place, move focus to parent
                if ($.contains($openCell.get(0), doc.activeElement)) {
                    $openCell.focus();
                }
            }

            /**
             * Opens a cell and records it
             * @param {Object} $td - The cell to open
             */
            function _open($td) {
                // Set this cell as open
                $openCell = $td;
                // Show!
                showHistory();
            }
        });
    };

})(window, document, jQuery);
