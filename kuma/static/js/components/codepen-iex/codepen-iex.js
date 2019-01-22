(function() {
    'use strict';
    var sampleCodeContainer = document.querySelector('.codepen-iex');

    /* only execute the rest of the code if there
       is a `sampleCodeContainer` on the page */
    if (sampleCodeContainer) {
        var tryItButton = document.createElement('button');
        tryItButton.classList.add('tryit');
        tryItButton.textContent = gettext('Try it live!');
        sampleCodeContainer.appendChild(tryItButton);

        // when the button is clicked
        tryItButton.addEventListener('click', function() {
            // call codepen to load the editor
            window.__CPEmbed('.codepen-iex');
            // hide the button
            tryItButton.classList.add('hidden');
        });
    }
})();
