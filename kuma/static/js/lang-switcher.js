(function (win, doc, $) {
    function storeLocaleChange(code, name) {
        localStorage.setItem('changed-locale-to', JSON.stringify({code: code, name: name}));
    }

    if(win.mdn.features.localStorage) {
        var langSwitcherSelector = document.getElementById('language'),
            langSwitcherButton = document.getElementById('translations');

        if (langSwitcherSelector) {
            langSwitcherSelector.addEventListener('change', function () {
                var element = this.options[this.options.selectedIndex];
                storeLocaleChange(element.dataset.locale, element.label);
            });
        }

        if (langSwitcherButton) {
            var transChoices = langSwitcherButton.querySelectorAll('li a');

            for (var i = 0; i < transChoices.length; i++) {

                transChoices[i].addEventListener('click', function () {
                    storeLocaleChange(this.dataset.locale, this.text);
                });
            }
        }

        // Insert notice about permanent language switch
        var changedLocaleTo = localStorage.getItem('changed-locale-to');
        if (changedLocaleTo) {
            var locale = JSON.parse(changedLocaleTo),
                text = gettext('You are now viewing this site in %(localeName)s.' +
                               ' Do you always want to view this site in %(localeName)s?'),
                html = interpolate(text +
                    '<br><button id="locale-permanent-yes" type="button" data-locale="%(localeCode)s">' +
                    gettext('Yes') + '</button> <button id="locale-permanent-no" type="button">' + gettext('No') +
                    '</button></p></div>', {localeCode: locale.code, localeName: locale.name}, true),
                notification = mdn.Notifier.growl(html, {closable: true, duration: 0}).question();

            // Add event listener to the buttons
            $('#locale-permanent-yes').on('click', function () {
                $.post('/i18n/setlang/', {language: this.dataset.locale})
                    .success(function () {
                        notification.close();
                        localStorage.removeItem('changed-locale-to');
                    });
            }
            );

            $('#locale-permanent-no').on('click', function () {
                notification.close();
                localStorage.removeItem('changed-locale-to');
            }
            );
        }
    }

})(window, document, jQuery);
