(function ($, win, doc) {
    'use strict';

    // feature test variable
    var supportsLocalStorage = win.mdn.features.localStorage;
    // some knowledge about the page we're dealing with
    var $translateForm = $('#translate-document');
    var $form = $translateForm.length ? $translateForm : $('#wiki-page-edit');
    var isNewTranslation = location.search.indexOf('tolocale') > -1 ? true : false;
    var publishUrl = function() {
        var thisUrl = win.location.href;
        return thisUrl.substring(0, thisUrl.indexOf('$'));
    }();
    var historyUrl = publishUrl + '$history';
    // stuff we need for drafts
    var DRAFT_NAME;
    var draftTimeOutId;
    var draftAutoSaveEnabled = true;
    var draftWait = false;
    var draftWaitTime = 500;
    var $revisionInputs = $('[name=current_rev]'); // can't use ID because there's a duplicate >_<
    // elements we need for communicating draft state
    var $draftDiv = $('<div/>', { class: 'draft-container' });
    var $draftOld = $('<div/>', { class: 'draft-old' });
    var $draftStatus = $('<div/>', { class: 'draft-status' });
    var $draftAction = $('<span/>', {id: 'draft-action'});
    var $draftTime = $('<time/>', {id: 'draft-time', class: 'time-ago'});
    var isErrors = $('.errorlist').length;
    var startingContent;


    /**
     * Generates a storage key based on pathname
     * Uses slashes as delimiters because they can't be used in slugs
     * to edge name clashes based on slug can be prevented
     */
    function draftStorageKey() {
        // start with path
        var key = location.pathname;
        // remove $vars
        key = key.replace('$edit', '');
        key = key.replace('$translate', '');

        key = 'draft/edit' + key;

        if (isNewTranslation) {
            // change translation creation format to match edit format
            // /en-US/docs/page$translate?tolocale=fr
            // draft/edit/fr/docs/page
            var localeCode = win.mdn.getUrlParameter('tolocale');
            key = key.replace('en-US', localeCode);
        }

        key = $.trim(key);
        return key;
    }

    // check for previous drafts, add recovery options
    function displayRestoreDraft(startingContent) {

        // look for previous draft
        var prevDraft = localStorage.getItem(DRAFT_NAME);
        var draftMatchesStart = contentMatches(prevDraft, startingContent);

        // if draft matches published version
        if (prevDraft && draftMatchesStart && !isErrors) {
            // don't need draft if it's a copy of the starting content
            clearDraft(false);
        }

        // if draft does not match current content, or if there are errors
        if (prevDraft && !draftMatchesStart) {
            var draftRevision = localStorage.getItem(DRAFT_NAME + '#revision');
            var draftTime = localStorage.getItem(DRAFT_NAME + '#save-time');
            var pageRevision = $revisionInputs.val();
            var draftTimeStr = draftTime ? draftTime : gettext('an unknown date');
            var view = gettext('View draft.');
            var restore = gettext('Restore draft.');
            var discard = gettext('Discard draft.');
            var draftWarning = '';
            var draftType;
            if(draftRevision === pageRevision || isNewTranslation) {
                // draft was created on this revision or is new translation
                draftType = 'current';
            } else if (draftRevision === '' && pageRevision !== '') {
                // draft of new translation that has since been published
                draftType = 'old';
            } else if (draftRevision !== null && draftRevision < pageRevision) {
                // revision string is out of date
                draftType = 'old';
            } else {
                // created before we were saving revision numbers
                // or something went wrong
                draftType = 'unknown';
            }

            if (draftType === 'old') {
                $draftOld.addClass('warning');
                draftWarning += '<div class="readable-line-length">';
                // long line is long, but breaking it up wrecks it for the localizers
                draftWarning += gettext('A newer version of this article has been published since this draft was saved. You can restore the draft to view the content, but you will not be able to submit it for publishing.');
                draftWarning += ' <a href="' + historyUrl + '" target="_blank" rel="noopener noreferrer" class="external-icon">' + gettext('Revision history.') + '</a> ';
                draftWarning += '<a href="' + publishUrl + '" target="_blank" rel="noopener noreferrer" class="external-icon">' + gettext('Published version') + '</a>';
                draftWarning += '</div>';

                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'outdated-draft-warning'
                });
            }

            if (draftType === 'unknown') {
                $draftOld.addClass('note');
                draftWarning += '<div class="readable-line-length">';
                // long line is long, but breaking it up wrecks it for the localizers
                draftWarning += gettext('Compare this date to the latest revision date to ensure you\'re not overwriting later changes.');
                draftWarning += ' <a href="' + historyUrl + '" target="_blank" rel="noopener noreferrer" class="external-icon">' + gettext('Revision history.') + '</a>';
                draftWarning += '</div>';

                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'unknown-draft-warning'
                });
            }

            var text = interpolate(gettext('You have a draft from: %(time)s.'), { time : draftTimeStr }, true);
            text += ' '; // add space incase buttons are next things added
            text += draftWarning;
            if (draftType !== 'old') {
                text += '<button type="button" class="js-restoreLink btn link">' + restore + '</button> ';
            } else {
                text += '<button type="button" class="js-viewLink btn link">' + view + '</button> ';
            }
            text += '<button type="button" class="js-discardLink btn link">'+ discard +'</button>';
            var $contentNode = $('#id_content');
            var editor;

            // Notify user of the existing draft
            $draftOld.empty();
            $draftOld.append(text);

            // Hook up the "view" link`
            $draftDiv.find('.js-viewLink').on('click', function() {
                if(draftRevision) {
                    $revisionInputs.val(draftRevision);
                }
                $contentNode.val(prevDraft);
                editor = $contentNode.ckeditorGet();
                editor.setData(prevDraft);
                editor.focus();
                // give user reminder they are just viewing old draft
                $draftOld.text(gettext('Viewing old draft. This draft cannot be published.'));
                saveDraft();

                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'view'
                });
            });

            // Hook up the "restore" link`
            $draftDiv.find('.js-restoreLink').on('click', function() {
                if(draftRevision) {
                    $revisionInputs.val(draftRevision);
                }
                $contentNode.val(prevDraft);
                editor = $contentNode.ckeditorGet();
                editor.setData(prevDraft);
                editor.focus();
                // inform user and remove old draft element
                $draftOld.text(gettext('Draft restored.')).delay(3000).slideUp();
                saveDraft();

                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'restore'
                });
            });

            // Hook up the "discard" link
            $draftDiv.find('.js-discardLink').on('click', function() {
                var currentDraftTime = localStorage.getItem(DRAFT_NAME + '#save-time');
                // only clear localstorage if no new draft created
                if(draftTime === currentDraftTime) {
                    clearDraft();
                }
                // inform user and remove old draft element
                $draftOld.text(gettext('Draft discarded.')).delay(3000).slideUp();

                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'discard'
                });

            });
        }
    }


    // Save button submits to top-level
    $form.on('submit', function () {
        if (supportsLocalStorage) {
            enableAutoSave(false);
            clearTimeout(draftTimeOutId);
        }
        return true;
    });


    // update the UI to reflect status of draft
    function updateDraftState(action) {
        var now = new Date();
        var nowString = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

        // delete old status
        $draftStatus.empty();

        if(action) {
            // text of message
            var update = '';
            if (action === 'published') {
                update = gettext('Draft published:');
            } else if (action === 'discarded') {
                update = gettext('Draft discarded:');
            } else if (action === 'autosaved') {
                update = gettext('Draft autosaved:');
            } else {
                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'error: unrecognized draft action'
                });
            }
            // clone elements and populate with message and time
            var $updateAction = $draftAction.clone().text(update);
            var $updateTime = $draftTime.clone().attr('title', now.toISOString()).text(nowString);
            // append elements
            $draftStatus.append($updateAction.append(' ').append($updateTime));
        }
    }

    function saveDraft(draftContent, draftState) {
        // put draft in local storage
        localStorage.setItem(DRAFT_NAME, draftContent);
        // put date of draft into local storage
        var now = new Date();
        var nowString = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();
        localStorage.setItem(DRAFT_NAME + '#save-time', nowString);
        // put revision id into local storage
        var revisionString = $revisionInputs.val();
        localStorage.setItem(DRAFT_NAME + '#revision', revisionString);
        // update UI
        updateDraftState(draftState);
    }

    // Throttle and debounce autosave
    function countDownToAutoSave () {
        // debounce - save draftWaitTime seconds after changes stop
        // clear old countdown to save
        clearTimeout(draftTimeOutId);
        // begin new countdown to save
        draftTimeOutId = setTimeout(autoSaveDraft, draftWaitTime);
        // throttle - save every 500ms
        if (!draftWait) {
            // save draft
            autoSaveDraft();
            // start wait before saving next time
            draftWait = true;
            setTimeout(function () {
                draftWait = false;
            }, draftWaitTime);
        }
    }

    function autoSaveDraft() {
        if(draftAutoSaveEnabled) {
            var currentContent = $form.find('textarea[name=content]').val();
            var oldDraft = localStorage.getItem(DRAFT_NAME);

            // it looks a little weird to save a draft when no changes are made
            // so check that what we're trying to save doesn't match what's
            // already saved
            var draftMatchesDraft = contentMatches(currentContent, oldDraft);
            // or hasn't actually changed
            var currentMatchesStart = contentMatches(currentContent, startingContent);

            if(!draftMatchesDraft && !currentMatchesStart) {
                saveDraft(currentContent, 'autosaved');
            }
        }
    }

    function clearDraft(notify) {
        localStorage.removeItem(DRAFT_NAME);
        localStorage.removeItem(DRAFT_NAME + '#save-time');
        localStorage.removeItem(DRAFT_NAME + '#revision');
        if (notify === 'publish') {
            updateDraftState('published');
        }
        else if (notify) {
            updateDraftState('discarded');
        }
        else {
            updateDraftState();
        }

    }

    // returns true if content matches
    // this is not perfect, CKEdtior adds white space even when the user hasn't edited
    function contentMatches(ver1, ver2) {
        var treatContent = function(content) {
            // CKEditor likes to change spaces for &nbsp;
            return content.replace(/\s/g, '&nbsp;');
        };
        var trim1 = $.trim(ver1);
        var treated1 = treatContent(trim1);
        var trim2 = $.trim(ver2);
        var treated2 = treatContent(trim2);
        if (treated1 === treated2) {
            return true;
        }
        else {
            return false;
        }
    }

    // change auto save status. Update variable and UI.
    function enableAutoSave(enabled) {
        // no change, no action needed
        if (enabled === draftAutoSaveEnabled) { return; }
        if (enabled === true) {
            //update variable
            draftAutoSaveEnabled = true;
            autoSaveDraft();
        } else {
            // update variable
            draftAutoSaveEnabled = false;
        }
    }

    // sets up drafting functionality
    function initDrafting() {

        if (supportsLocalStorage) {
            DRAFT_NAME = draftStorageKey();
            if (DRAFT_NAME === null) { return false; }

            /**
             *  Data migration for draft keys
             */

            var localeRegEx = /(\/)([a-zA-Z]+-?[a-zA-Z]*)?(#|$)/;

            // loop through localstorage making array of old keys
            var oldKeys = [];
            for (var i = 0; i < localStorage.length; i++) {
                var keyName = localStorage.key(i);
                if(keyName.indexOf('draft/translate/') === 0) {
                    oldKeys.push(keyName);
                }
            }
            // loop through old keys, making new key & values
            for (var j = 0; j < oldKeys.length; j++){
                // make new key
                var newKey = oldKeys[j];
                // replace /translate/ with /edit/
                newKey = newKey.replace('draft/translate/', 'draft/edit/');
                // get locale from end of string
                var findLocale = localeRegEx.exec(newKey);
                // replace `/locale/` with just a `/`
                newKey = newKey.replace(localeRegEx, '$3');
                // this only works if a locale was found
                try {
                    // capture locale
                    var locale = findLocale[2];
                    // replace en-US with locale
                    newKey = newKey.replace('/en-US/', '/' + locale + '/');
                } catch (err) {
                    // nada
                }

                // save content with new key
                localStorage.setItem(newKey, localStorage.getItem(oldKeys[j]));

                // delete old key
                localStorage.removeItem(oldKeys[j]);

                // track data conversion
                // so we get some idea of when we can pull this code out
                mdn.analytics.trackEvent({
                    category: 'draft',
                    action: 'data-conversion'
                });
            }

            /**
             * Add draft UI
             */


            // insert UI elements
            $draftDiv.append(' ');
            $draftDiv.append($draftOld);
            $draftDiv.append($draftStatus);

            // inform user autosave enabled
            $draftStatus.text(gettext('Autosave enabled.'));
            $('#editor-wrapper').prepend($draftDiv);

            // check for old draft to restore
            startingContent = $form.find('textarea[name=content]').val();
            displayRestoreDraft(startingContent);

            /**
             * Event listeners
             */

            // Add key listener for CKEditor and drafting
            try {
                var $content = $('#id_content');
                if($content.ckeditorGet) {
                    $content.ckeditorGet().on('change', countDownToAutoSave);
                }
            }
            catch(e) {
                // console.log(e);
            }

            // Clear draft upon discard
            $('.btn-discard').on('click', function() {
                clearTimeout(draftTimeOutId);
                clearDraft(true);
                // don't save any more drafts, we're done here
                enableAutoSave(false);
            });

            // Remove old draft & meta info, report publish.
            $form.on('mdn:save-success', function() {
                clearDraft('publish');
            });

        }
    }

    $(doc).ready(function(){
        // drafts only work on certian pages
        if ($('body').is('.edit, .translate')) {
            initDrafting();
        }
    });

}(jQuery, window, document));
