(function() {
    'use strict';

    var otherEmailInput = document.getElementById('id_other_email');
    var signupForm = document.getElementById('social-signup-form');

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
