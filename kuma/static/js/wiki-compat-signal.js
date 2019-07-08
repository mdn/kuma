(function() {
    'use strict';

    var bcTable;

    /**
     * Creates and returns the signal element HTML
     * @returns signal element HTML
     */
    function signalElem() {
        const extContainer = document.createElement('div');
        const separator = document.createElement('hr');
        const container = document.createElement('div');
        const signalLink = document.createElement('a');
        signalLink.textContent = 'Flag as incorrect';
        const signalApiUrl = '/api/v1/bc-signal';

        const payload = {
            'slug': document.body.dataset.slug,
            'locale': window.location.pathname.split('/')[1]
        };

        signalLink.addEventListener('click', function() {
            fetch(signalApiUrl, {
                method: 'POST',
                body: JSON.stringify(payload),
                headers: {
                    'X-CSRFToken': mdn.utils.getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            }).then(function() {
                signalLink.textContent = 'Thank you for letting us know!';
            }).catch(function() {
                signalLink.textContent = 'Something went wrong!';
            }).then(function() {
                setTimeout(function() {
                    container.classList.add('slideUp');
                }, 1000);
            });
        });

        container.setAttribute('class', 'signal-link-container');
        extContainer.setAttribute('class', 'signal-link-ext-container');
        container.appendChild(separator);
        container.appendChild(signalLink);
        extContainer.appendChild(container);
        return extContainer;
    }

    bcTable = document.querySelector('.bc-table');
    bcTable.insertAdjacentElement('afterend', signalElem());
})();
