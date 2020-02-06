(function() {
    'use strict';

    var deleteUserModalContainer = document.getElementById('delete-user-modal');

    if (
        !deleteUserModalContainer ||
        !window.mdn.modalDialog.shouldShowModal()
    ) {
        return;
    }

    var cancelButton = deleteUserModalContainer.querySelector('#cancel-button');
    var closeModalButton = deleteUserModalContainer.querySelector(
        '.close-modal'
    );
    var deleteUserButton = document.getElementById('delete-user-button');

    function handleKeyup(event) {
        if (event.key === 'Escape') {
            closeModalButton.click();
        }
    }

    if (deleteUserButton) {
        /* toggling of delete confirmation button is handled in
           kuma/static/js/components/account-management/delete-user-confirmation-button.js */

        deleteUserButton.addEventListener('click', function(event) {
            event.preventDefault();

            var modalContentContainer = deleteUserModalContainer.querySelector(
                '.delete-user'
            );

            deleteUserModalContainer.classList.remove('hidden');
            modalContentContainer.focus();

            window.mdn.modalDialog.handleKeyboardEvents(
                deleteUserModalContainer
            );
            document.addEventListener('keyup', handleKeyup);
        });

        closeModalButton.addEventListener('click', function(event) {
            window.mdn.modalDialog.closeModal(
                deleteUserModalContainer,
                event.target
            );
            document.removeEventListener('keyup', handleKeyup);
        });

        cancelButton.addEventListener('click', function(event) {
            window.mdn.modalDialog.closeModal(
                deleteUserModalContainer,
                event.target
            );
        });
    }
})();
