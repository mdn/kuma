(function ($) {
    'use strict';

    var $revisionReplaceBlock = $('#revision-replace-block');
    var $localeInput = $('#id_locale');
    var $filterForm = $('#revision-filter');
    var $pageInput = $('#revision-page');
    var currentLocale = $('html').attr('lang');

    /**
     * Builds and returns an individual list item
     * @param {Object} properties - A properties object with values
     * for the attibutes of the anchor element
     * Example
     * --------
     * {
     *   id: 'revert',
     *   href: controlURLs.revertURL,
     *   text: gettext(actionsArray[i]),
     *   icon: 'undo'
     * }
     * @returns The list element as a `HTMLElement`
     */
    function getListItem(properties) {
        var listItem = document.createElement('li');
        var anchor = document.createElement('a');
        anchor.setAttribute('id', properties.id);
        anchor.setAttribute('href', properties.href);
        anchor.classList.add('button');
        anchor.textContent = properties.text;
        anchor.append(window.mdnIcons ? window.mdnIcons.getIcon(properties.icon) : '');
        return listItem.appendChild(anchor);
    }

    /**
     * Builds and returns all the action buttons as an unordered list
     * @param {Object} controlURLs - The url for each action
     * @returns An unordered list with action buttons as a `HTMLElement`
     */
    function getActionButtons(controlURLs) {
        var actionsArray = ['Revert', 'View Page', 'Edit Page', 'History'];
        var pageButtons = document.createElement('ul');
        pageButtons.setAttribute('id', 'page-buttons');

        for (var i = 0, l = actionsArray.length; i < l; i++) {
            if (actionsArray[i] === 'Revert') {
                pageButtons.appendChild(getListItem({
                    id: 'revert',
                    href: controlURLs.revertURL,
                    text: gettext('Revert'),
                    icon: 'undo'
                }));
            }

            if (actionsArray[i] === 'View Page') {
                pageButtons.appendChild(getListItem({
                    id: 'view',
                    href: controlURLs.viewURL,
                    text: gettext('View Page'),
                    icon: 'play'
                }));
            }

            if (actionsArray[i] === 'Edit Page') {
                pageButtons.appendChild(getListItem({
                    id: 'edit',
                    href: controlURLs.editURL,
                    text: gettext('Edit Page'),
                    icon: 'pencil'
                }));
            }

            if (actionsArray[i] === 'History') {
                pageButtons.appendChild(getListItem({
                    id: 'history',
                    href: controlURLs.historyURL,
                    text: gettext('History'),
                    icon: 'book'
                }));
            }
        }

        return pageButtons;
    }

    /**
     * Builds and returns the actions bar setting urls as specified
     * in the `controlURLs` object
     * @param {Object} controlURLs - URLs to set for the various controls
     * Example
     * --------
     * {
     *   revertURL: 'https://...',
     *   viewURL: 'https://...',
     *   editURL: 'https://...',
     *   historyURL: 'https://...'
     * }
     * @returns controls wrapped in a `div` elemtn as a Node
     */
    function getActionsBar(controlURLs) {
        var actionBar = document.createElement('div');
        actionBar.setAttribute('class', 'action-bar');
        return actionBar.appendChild(getActionButtons(controlURLs));
    }

    // Create the autocomplete for user
    $('#id_user').mozillaAutocomplete({
        minLength: 3,
        labelField: 'label',
        autocompleteUrl: '/' + currentLocale + '/dashboards/user_lookup',
        buildRequestData: function (req) {
            // Should add locale value here
            req.locale = getFilterLocale();
            req.user = req.term;
            return req;
        }
    });

    // Create the autocomplete for topic
    $('#id_topic').mozillaAutocomplete({
        minLength: 3,
        labelField: 'label',
        autocompleteUrl: '/' + currentLocale + '/dashboards/topic_lookup',
        buildRequestData: function (req) {
            // Should add locale value here
            req.locale = getFilterLocale();
            req.topic = req.term;
            return req;
        }
    });

    // Enable keynav
    $revisionReplaceBlock.mozKeyboardNav({
        itemSelector: '.dashboard-row',
        onEnterKey: function (item) {
            $(item).trigger('mdn:click');
        },
        alwaysCollectItems: true
    });

    // Focus on the first item, if there
    focusFirst();
    // Wire Show IPs button if there
    connectShowIPs();

    // Create date pickers
    $('#id_start_date, #id_end_date').datepicker();

    // When an item is clicked, load its detail
    $revisionReplaceBlock.on('click mdn:click', '.dashboard-row', function (e) {
        var $this = $(this);

        // Don't interrupt links or spam buttons, and stop if a request is already running
        if (e.target.tagName === 'A' || $(e.target).hasClass('spam-ham-button') || $this.attr('data-running')) {
            return;
        }

        if ($this.attr('data-loaded')) {
            $this.next('.dashboard-detail').find('.dashboard-detail-details').slideToggle();
        } else {
            $this.attr('data-running', 1);
            $.ajax({
                url: $this.attr('data-compare-url')
            }).then(function (content) {
                // Prepend the controls
                var controls = getActionsBar({
                    revertURL: $this.attr('data-revert-url'),
                    viewURL: $this.attr('data-view-url'),
                    editURL: $this.attr('data-edit-url'),
                    historyURL: $this.attr('data-history-url')
                });

                var row = document.createElement('tr');
                row.classList.add('dashboard-detail');

                var column = document.createElement('td');
                column.setAttribute('colspan', '5');

                var div = document.createElement('div');
                div.classList.add('dashboard-detail-details');

                div.appendChild(controls);
                div.appendChild($(content)[0]);

                column.appendChild(div);
                row.appendChild(column);

                var currentRow = $this[0];

                currentRow.insertAdjacentElement('afterend', row);

                $this.next('.dashboard-detail').find('.dashboard-detail-details').slideToggle();
                $this.attr('data-loaded', 1);
                $this.removeAttr('data-running');
            });
        }
    });

    // AJAX loads for pagination
    $revisionReplaceBlock.on('click', '.pagination a', function (e) {
        e.preventDefault();
        var pageNum = /page=([^&#]*)/.exec(this.href)[1];
        var linkText = this.text.trim();
        mdn.analytics.trackEvent({
            category: 'Dashboard Pagination',
            action: pageNum,
            label: linkText
        });
        $pageInput.val(pageNum);
        $filterForm.submit();
    });

    // Filter form submission handler; loads content via AJAX, updates URL state
    $filterForm.on('submit', function (e) {
        e.preventDefault();
        var $this = $(this);

        if ('pushState' in history) {
            history.pushState(null, '', location.pathname + '?' + $this.serialize());
        }

        var notification = mdn.Notifier.growl(gettext('Hang on! Updating filters…'), { duration: 0 });
        $.ajax({
            url: $this.attr('action'),
            data: $this.serialize()
        }).then(function (content) {
            replaceContent(content);
            $this.trigger('ajaxComplete');
            notification.success(gettext('Updated filters.'), 2000);
            // Reset the page count to 0 in case of new filter
            $pageInput.val(1);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            notification.error(gettext('Error loading content, please refresh the page'), 5000);
            console.error('Error thrown while loading content: ' + textStatus, errorThrown);
        });
    });

    // Send revision to Akismet for Spam or Ham
    $(document).on('click', '.spam-ham-button', function() {
        var $this = $(this),
            $tdObject = $(this).parent(),
            $trObject = $tdObject.parent(),
            revisionId = $trObject.data('revisionId'),
            type = this.value,
            url = $trObject.data('spamUrl');

        $this.prop('disabled', true);
        $tdObject.find('.error , .submit').remove();
        $tdObject.append('<strong class="submit"><br>' + gettext('Submitting...') + '</strong>');

        $.post(url, {'revision': revisionId, 'type': type})
            .done( function(data) {
                var $dl = $('<dl></dl>');

                $.each(data, function(index, value) {
                    var subMessage = '<dt class="submission-' + value.type + '">' +
                  interpolate(gettext('Submitted as %(submissionType)s'), {
                      submissionType: value.type
                  }, true) + '</dt><dd>' +
                  interpolate(gettext('%(sentDate)s by %(user)s'), {
                      sentDate: value.sent, user: value.sender
                  }, true);

                    $dl.append(subMessage);
                });

                $tdObject.html($dl);

            })
            .fail( function() {
                $this.prop('disabled', false);
                var errorMessage = '<strong class="error"><br>' + interpolate(gettext('Error submitting as %(type)s'), {type: type}, true) + '</strong>';

                $tdObject.find('.error , .submit').remove();
                $tdObject.append(errorMessage);
            });

    });

    // Wire Toggle IPs button, if present
    function connectShowIPs() {
        $('#show_ips_btn').on('click', function() {
            $('.revision_ip').slideToggle();
        });
    }

    // Returns the revision locale filter value
    function getFilterLocale() {
        return $localeInput.get(0).value || currentLocale;
    }

    // Focuses on the first row in the table
    function focusFirst() {
        var $first = $revisionReplaceBlock.find('.dashboard-row').first();
        if($first.length) {
            $first.get(0).focus();
        }
    }

    // Replaces table body content and scrolls to top of the page
    function replaceContent(content) {
        $revisionReplaceBlock.fadeOut(function () {
            $(this).html(content).fadeIn(function () {
                focusFirst();
                connectShowIPs();
            });

            // Animate to top!
            $('html, body').animate({
                scrollTop: $revisionReplaceBlock.offset().top
            }, 2000);
        });
    }

})(jQuery);
