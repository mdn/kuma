(function($) {

    // Private var to assign IDs to history for accessibility purposes
    var historyCount = 0;

    // The close button template
    var $historyCloseButton = $('<button><abbr><span></span><i></i></abbr></button>')
                              .addClass('bc-history-button')
                              .find('abbr')
                                .addClass('only-icon')
                                .attr('title', gettext('Return to compatability table.'))
                                .end()
                              .find('span')
                                .append(gettext('Close'))
                              .end()
                              .find('i')
                                .addClass('icon-times')
                                .attr('aria-hidden', true)
                              .end();

    // Slide requires delay for designed effect
    var openDelay = 10;
    var closeDelay = 200;

    //  Usage: $('.compat-table').mozCompatTable();
    return jQuery.fn.mozCompatTable = function() {
        return $(this).each(function() {

            // Keep track of what may be open within this table
            var $openCell;

            // If nothing provided, bail
            var $table = $(this);
            if(!$table.length) return;

            // Activate all history cells for keyboard;  TODO:  add "aria-controls"
            $table.find('.bc-has-history').each(function() {
                var historyId = 'bc-history-' + (++historyCount);
                var $td = $(this);

                $td.attr({
                    tabIndex: 0,
                    'aria-expanded': false,
                    'aria-controls': historyId
                });
                $td.find('.bc-history').attr('id', historyId);
                $td.find('.bc-history-link').attr('tabIndex', -1);
            });

            // Listen for clicks on "history" cells
            $table.on('click', '.bc-has-history, .bc-history', function() {
                var $target = $(this);

                if($target.hasClass('.bc-history')) {
                    e.stopImmediatePropagation();
                }
                closeAndOpenHistory($target);
            });

            // Listen for clicks on "close" buttons
            $table.on('click', '.bc-history-button', function(ev) {
                ev.stopImmediatePropagation();
                hideHistory();
            });

            // Listen for keys to open/close history
            $table.on('keypress', '.bc-has-history', function(ev) {
                var $td = $(this);
                var key = ev.which;

                if(key === 13 || key === 32) {
                    closeAndOpenHistory($td);
                    ev.preventDefault();
                } else if(key === 27) {
                    hideHistory();
                    ev.preventDefault();
                }
            });


            // Function which closes any open history, opens the target history
            function closeAndOpenHistory($td) {
                var previousOpenCell = $openCell && $openCell.get(0);

                // Close what's open, if anything
                hideHistory();

                // If they clicks the same cell (are closing), we can leave now
                if($td.get(0) == previousOpenCell) {
                    $openCell = false;
                    return;
                }

                // Set this cell as open
                $openCell = $td;

                // Show!
                showHistory();
            }


            // Opens the history for a given item
            function showHistory() {

                var $row = $openCell.closest('tr');
                var $history = $openCell.find('.bc-history').outerWidth($table.width());

                // get cell coords
                var cellLeft = $openCell.offset().left;

                // get cell left border
                var cellLeftBorder = $openCell.css('border-left-width');

                // get table coords
                var tableLeft = $table.offset().left;

                // left coord of table minus left coord of cell
                var historyLeft = tableLeft - cellLeft - parseInt(cellLeftBorder, 10) - 1;

                // top
                // can't just to top:100% in CSS because IE messes it up.

                // get cell height
                var cellTop = $openCell.outerHeight();

                // get cell top border
                var celltopBorder = $openCell.css('border-top-width');

                // get cell bottom border
                var cellBottomBorder = $openCell.css('border-bottom-width');

                var historyTop = cellTop - parseInt(cellBottomBorder, 10) - parseInt(celltopBorder, 10);

                var historyHeight;
                var windowWidth;

                // Add a close button if one doesn't already exist
                if($history.find('.bc-history-button').length === 0) {
                    $historyCloseButton.clone().appendTo($history);
                }

                // move history where it will display
                $history.css({
                    left: historyLeft,
                    top: historyTop
                });

                // measure height
                $history.css('display', 'block');
                $history.attr('aria-hidden', false);

                historyHeight = $history.outerHeight();

                // set max-height to 0 and visibility to visible
                $openCell.addClass('active');
                $openCell.attr('aria-expanded', true);

                setTimeout(function() {
                    $history.css('height', historyHeight);

                    // add measured height to history and to the cell/row it is being displayed beneath (CSS handles transition)
                    windowWidth = window.innerWidth;
                    if(windowWidth > 801) {
                        $row.find('th, td').css('border-bottom', historyHeight + 'px solid transparent');
                    } if(windowWidth > 481) {
                        $row.find('td').css('border-bottom', historyHeight + 'px solid transparent');
                    } else {
                        $openCell.css('border-bottom', historyHeight + 'px solid transparent');
                    }
                }, openDelay);
            }

            // Hides the history dropdown for a given cell
            function hideHistory(){
                var $history, $delayCloseCell;

                if(!$openCell) return;

                $openCell.css('border-bottom', '').attr('aria-expanded', false);
                $openCell.closest('tr').find('th, td').css('border-bottom', '');

                $history = $openCell.find('.bc-history');
                $history.css('height', '').attr('aria-hidden', true);

                // if the focus is inside the .bc-history and we'd lose our keyboard place, move focus to parent
                if($.contains($openCell.get(0), document.activeElement)) {
                    $openCell.focus();
                }

                $delayCloseCell = $openCell;
                setTimeout(function() {
                    $delayCloseCell.removeClass('active');
                    $history.css('display', 'none');
                }, closeDelay);
            }
        });
    };

})(jQuery);
