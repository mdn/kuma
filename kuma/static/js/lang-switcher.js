(function (win, doc, $) {
    var sessionStorageKey = 'changed-locale-to';
    function storeLocaleChange(code, name) {
        sessionStorage.setItem(sessionStorageKey, JSON.stringify({code: code, name: name}));
    }

    function removeLocaleChange() {
        sessionStorage.removeItem(sessionStorageKey);
    }

    function getLocaleChange() {
        return sessionStorage.getItem(sessionStorageKey);
    }

    if(win.sessionStorage) {
        var langSwitcherSelector = document.getElementById('language');
        var langSwitcherButton = document.getElementById('translations');

        if (langSwitcherSelector) {
            langSwitcherSelector.addEventListener('change', function() {
                var element = this.options[this.options.selectedIndex];
                storeLocaleChange(element.dataset.locale, element.label);
            });
        }

        if (langSwitcherButton) {
            var transChoices = langSwitcherButton.querySelectorAll('li a');

            for (var i = 0; i < transChoices.length; i++) {
                transChoices[i].addEventListener('click', function() {
                    storeLocaleChange(this.dataset.locale, this.text);
                });
            }
        }

        // Insert notice about permanent language switch
        var changedLocaleTo = getLocaleChange();
        if (changedLocaleTo) {
            var locale = JSON.parse(changedLocaleTo);
            var text = gettext('You are now viewing this site in %(localeName)s.' +
                               ' Do you always want to view this site in %(localeName)s?');
            var html = interpolate(text +
                    '<br><button id="locale-permanent-yes" type="button" data-locale="%(localeCode)s">' +
                    gettext('Yes') + '</button> <button id="locale-permanent-no" type="button">' + gettext('No') +
                    '</button></p></div>', {localeCode: locale.code, localeName: locale.name}, true);
            var notification = mdn.Notifier.growl(html, {closable: true, duration: 0});
            notification.question();
            removeLocaleChange();

            // Add event listener to the buttons
            $('#locale-permanent-yes').on('click', function() {
                $.post('/i18n/setlang/', {language: this.dataset.locale})
                    .success(function() {
                        notification.close();
                    });
            });

            $('#locale-permanent-no').on('click', function() {
                notification.close();
            });
        }
    }
})(window, document, jQuery);
