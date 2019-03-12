(function() {
    'use strict';
    var contributeForm = document.getElementById('contribute-form');

    /**
     * Removes the `focus-visible` class form the current element
     */
    function removeFocusVisible() {
        this.classList.remove('focus-visible');
        this.removeEventListener('focusout', removeFocusVisible);
    }

    if (contributeForm) {
        // When a keyup event is triggered on the contribute form,
        contributeForm.addEventListener('keyup', function(event) {
            var currentTarget = event.target;
            var targetType = currentTarget.type;

            /* The key pressed was the tab key, or the left or right
               arrow keys(used to cycle through radio buttons), and the
               target field type is one of `radio` */
            if (
                (event.key === 'Tab' ||
                    event.key === 'ArrowLeft' ||
                    event.key === 'ArrowRight') &&
                targetType === 'radio'
            ) {
                // get the parent label element
                var radioButtonLabel = currentTarget.parentElement;
                // add the `focus-visible` class
                radioButtonLabel.classList.add('focus-visible');
                // listen for when the field loses focus,
                radioButtonLabel.addEventListener(
                    'focusout',
                    removeFocusVisible
                );
            }

            /* The key pressed was the tab key, and the target field
               type is one of `text`, `email`, or `number */
            if (
                event.key === 'Tab' &&
                (targetType === 'text' ||
                    targetType === 'email' ||
                    targetType === 'number')
            ) {
                // add the `focus-visible` class.
                currentTarget.classList.add('focus-visible');
                // listen for when the field loses focus,
                currentTarget.addEventListener('focusout', removeFocusVisible);
            }
        });
    }
})();
