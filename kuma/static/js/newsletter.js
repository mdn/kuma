(function(doc) {
    'use strict';

    // !! this file assumes only one signup form per page !!

    var newsletterForm = doc.getElementById('newsletterForm');
    var isHidden = false;
    var isArticle = false;

    if(!newsletterForm) {
        return;
    } else {
        // check for local storage
        if(mdn.features.localStorage) {
            // if hidden by local storage
            isHidden = localStorage.getItem('newsletterHide') === 'true' ? true : false;
        }

        // check for article
        if(doc.querySelector('#wikiArticle')) {
            isArticle = true;
        }

        if(!mdn.features.localStorage || !isArticle) {
            newsletter();
        } else if(isArticle && !isHidden) {
            newsletter();
            newsletterAddHideButton();
        } else if (isArticle && isHidden) {
            newsletterHide();
        }
    }

    function newsletter() {
        var newsletterEmailInput = doc.getElementById('newsletterEmailInput');
        var newsletterPrivacy = doc.getElementById('newsletterPrivacy');

        // handle errors
        var errorArray = [];
        var newsletterErrors = doc.getElementById('newsletterErrors');

        function newsletterError() {
            if(errorArray.length) {
                showFormErrors(errorArray);
            } else {
                // no error messages, forward to server for better troubleshooting
                newsletterForm.setAttribute('data-skip-xhr', true);
                newsletterForm.submit();
            }
        }

        function showFormErrors(errorArray) {
            var errorList = doc.createElement('ul');
            errorList.className = 'errorlist';

            for (var i = 0, l = errorArray.length; i < l; i++) {
                var item = doc.createElement('li');
                item.appendChild(doc.createTextNode(errorArray[i]));
                errorList.appendChild(item);
            }
            newsletterErrors.appendChild(errorList);
            $(newsletterErrors).removeClass('hidden');
            // track an error happened
            mdn.analytics.trackEvent({
                'category': 'newsletter',
                'action': 'progression',
                'label': 'error'
            });
        }

        // show success message
        function newsletterThanks() {
            // hide form
            $(newsletterForm).addClass('hidden');
            // show thanks message
            $('#newsletterThanks').removeClass('hidden');
            // hide close button, analytics get confusing if it stays
            $('#newsletterHide').addClass('hidden');
            // track success
            mdn.analytics.trackEvent({
                'category': 'newsletter',
                'action': 'progression',
                'label': 'complete'
            });
            // don't show signup form on article pages anymore
            newsletterSaveHide();
        }

        // XHR subscribe; handle errors; display thanks message on success.
        function newsletterSubscribe(event) {
            var skipXHR = newsletterForm.getAttribute('data-skip-xhr');
            if (skipXHR) {
                // track this
                mdn.analytics.trackEvent({
                    'category': 'newsletter',
                    'action': 'progression',
                    'label': 'error-forward'
                });

                return true;
            }
            event.preventDefault();
            event.stopPropagation();

            // track this submission
            mdn.analytics.trackEvent({
                'category': 'newsletter',
                'action': 'progression',
                'label': 'submission'
            });

            // new submission, clear old errors
            errorArray = [];
            $(newsletterErrors).addClass('hidden');
            while (newsletterErrors.firstChild) {
                newsletterErrors.removeChild(newsletterErrors.firstChild);
            }

            var fmt = doc.getElementById('fmt').value;
            var email = newsletterEmailInput.value;
            var newsletter = doc.getElementById('newsletterNewslettersInput').value;
            var privacy = doc.querySelector('input[name="privacy"]:checked') ? '&privacy=true' : '';
            var params = 'email=' + encodeURIComponent(email) +
                         '&newsletters=' + newsletter +
                         privacy +
                         '&fmt=' + fmt +
                         '&source_url=' + encodeURIComponent(doc.location.href);

            var xhr = new XMLHttpRequest();

            xhr.onload = function(r) {
                if (r.target.status >= 200 && r.target.status < 300) {
                    // response is null if handled by service worker
                    if(response === null) {
                        newsletterError(new Error());
                        return;
                    }
                    var response = r.target.response;
                    if (response.success === true) {
                        newsletterThanks();
                    } else {
                        if(response.errors) {
                            for (var i = 0, l = response.errors.length; i < l; i++) {
                                errorArray.push(response.errors[i]);
                            }
                        }
                        newsletterError(new Error());
                    }
                }
                else {
                    newsletterError(new Error());
                }
            };

            xhr.onerror = function(event) {
                newsletterError(event);
            };

            var url = newsletterForm.getAttribute('action');

            xhr.open('POST', url, true);
            xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
            xhr.setRequestHeader('X-Requested-With','XMLHttpRequest');
            xhr.timeout = 5000;
            xhr.ontimeout = newsletterError;
            xhr.responseType = 'json';
            xhr.send(params);

            return false;
        }

        newsletterForm.addEventListener('submit', newsletterSubscribe, false);

        newsletterEmailInput.addEventListener('focus', function() {
            $(newsletterPrivacy).removeClass('hidden');
            mdn.analytics.trackEvent({
                'category': 'newsletter',
                'action': 'prompt',
                'label': 'focus'
            });
        }, false);
    }

    function newsletterAddHideButton() {
        var $hideButton = $('#newsletterHide');
        // show button
        $hideButton.removeClass('hidden');
        // add listener
        $hideButton.on('click', newsletterHandleHideClick);
    }

    function newsletterHide() {
        var $newsletterBox = $('.newsletter-box');
        $newsletterBox.addClass('hidden');
    }

    function newsletterSaveHide() {
        localStorage.setItem('newsletterHide', true);
    }

    function newsletterHandleHideClick() {
        newsletterHide();
        newsletterSaveHide();
        mdn.analytics.trackEvent({
            'category': 'newsletter',
            'action': 'prompt',
            'label': 'hide'
        });
    }

})(document);
