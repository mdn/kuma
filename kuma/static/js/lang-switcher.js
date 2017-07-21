(function () {
    var langSwitcherSelector = document.getElementById('language'),
        langSwitcherButton = document.getElementById('translations');

    function storeLocaleChange(code, name) {
        localStorage.setItem('changed-locale-to', JSON.stringify({code: code, name: name}));
    }

    if (langSwitcherSelector) {
        langSwitcherSelector.addEventListener('change', function () {
            var element = this.options[this.options.selectedIndex];
            storeLocaleChange(element.dataset.locale, element.label);
        });
    }

    if (langSwitcherButton) {
        var transChoices = langSwitcherButton.querySelectorAll('li a');

        for(var i = 0; i < transChoices.length; i++) {

            transChoices[i].addEventListener('click', function () {
                storeLocaleChange(this.dataset.locale, this.text);
            });
        }
    }

})();
