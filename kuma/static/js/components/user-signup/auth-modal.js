(function() {
    'use strict';

    var authModalContainer = document.getElementById('auth-modal');

    if (
        !authModalContainer ||
        !window.mdn.modalDialog.shouldShowModal()
    ) {
        return;
    }

    var authTextElement = authModalContainer.querySelector('p');
    var originalText = authTextElement.textContent;

    function triggerAuthModal(textOverride) {

        function handleKeyup(event) {
            if (event.key === 'Escape') {
                closeModalButton.click();
            }
        }

        if (textOverride && textOverride !== originalText) {
            authTextElement.textContent = textOverride;
        }

        var closeModalButton = document.getElementById('close-modal');
        var modalContentContainer = authModalContainer.querySelector('section');
        authModalContainer.classList.remove('hidden');
        modalContentContainer.focus();

        closeModalButton.addEventListener('click', function() {
            window.mdn.modalDialog.closeModal(authModalContainer);
            document.removeEventListener('keyup', handleKeyup);

            if (textOverride && textOverride !== originalText) {
                authTextElement.textContent = originalText;
            }
        });

        window.mdn.modalDialog.handleKeyboardEvents(authModalContainer);

        document.addEventListener('keyup', handleKeyup);

    }

    window.mdn.triggerAuthModal = triggerAuthModal;

})();
