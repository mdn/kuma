(function() {
    'use strict';

    var otherEmailInput = document.getElementById('id_other_email');
    var signupForm = document.getElementById('social-signup-form');

    /**
     * A simple test to determine if `onanimationend` is supported
     * @returns {Boolean}
     */
    function isOnAnimationEndSupported() {
        var elem = document.createElement('img');
        return 'onanimationend' in elem;
    }

    /**
     * Hides the specified static content container, shows the edit
     * container and sets focus to the specified element.
     * @param {Object} staticContainer - The container to hide
     * @param {Object} editContainer - The container to show
     * @param {Object} focusElement - The element to focus
     */
    function showEditFields(staticContainer, editContainer, focusElement) {
        staticContainer.classList.add('hidden');
        editContainer.classList.remove('hidden');
        focusElement.focus();
    }

    /**
     * Adds checkmark to MDN auth avatar, loads and animates the users Github avatar
     * @param {HTMLFormElement} form - The form to submit after `onanimationend`
     */
    function animateAvatar(form) {
        var avatarURL = event.target.dataset['avatar'];
        var mdnProfileImgContainer = document.querySelector('.mdn-profile');
        var mdnProfileImg = mdnProfileImgContainer.querySelector('img');

        mdnProfileImg.src = avatarURL;
        mdnProfileImg.addEventListener('load', function() {
            mdnProfileImgContainer.classList.add('checked');
            mdnProfileImg.classList.add('animate');

            mdnProfileImg.onanimationend = function() {
                form.submit();
            };
        });
    }

    signupForm.addEventListener('click', function(event) {
        var editContainer;
        var focusElement;
        var staticContainer;

        if (event.target.id === 'change-username') {
            staticContainer = document.getElementById(
                'username-static-container'
            );
            editContainer = document.getElementById(
                'change-username-container'
            );
            focusElement = editContainer.querySelector('input');
            showEditFields(staticContainer, editContainer, focusElement);
        } else if (event.target.id === 'change-email') {
            staticContainer = document.getElementById('email-static-container');
            editContainer = document.getElementById('change-email-container');
            focusElement = editContainer.querySelector('label');
            showEditFields(staticContainer, editContainer, focusElement);
        } else if (event.target.id === 'create-mdn-account') {
            if (isOnAnimationEndSupported()) {
                event.preventDefault();
                animateAvatar(signupForm);
            } else {
                var mdnProfileImgContainer = document.querySelector('.mdn-profile');
                mdnProfileImgContainer.classList.add('checked');
            }
        }
    });

    /* when the "other" email input field lose focus, set its
       associated radio button to the checked state if the
       data entered was valid */
    if (otherEmailInput) {
        otherEmailInput.addEventListener('blur', function(event) {
            if (event.target.validity.valid) {
                event.target.parentElement.querySelector(
                    'input[type="radio"]'
                ).checked = true;
            }
        });
    }
})();
