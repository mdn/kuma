
(function(win, doc) {
    'use strict';

    var path = win.location.pathname;
    if (!path.includes('/payments/recurring/management')) {
        return;
    }

    var toggleConfirmationButtons = Array.from(doc.querySelectorAll('button[tooggle-confirmation]'));
    var confirmationDialog = doc.getElementById('delete-confirmation');

    /**
     * Toggle the visibility of the confirmation dialog
     */
    function toggleDeleteConfirmaiton() {
        toggleConfirmationButtons[0].classList.toggle('hidden');
        confirmationDialog.classList.toggle('hidden');
    }

    toggleConfirmationButtons.forEach(function(button) {
        button.addEventListener('click', toggleDeleteConfirmaiton);
    });

})(window, document);
