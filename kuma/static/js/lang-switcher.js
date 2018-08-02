(function (win, doc, $) {
    var sessionStorageKey = 'changed-locale-to';
    var neverShowNoticeKey = 'never-show-locale-notice';
    var neverShowNotice = getNeverShowNotice();
    function storeLocaleChange(code, name) {
        if (!isLocalePreference(code)){
            sessionStorage.setItem(sessionStorageKey, JSON.stringify({code: code, name: name}));
        }
    }

    function getCookie(name) {
        var match = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
        return match ? match[2] : null;
    }

    function isLocalePreference(code) {
        return getCookie(win.mdn.langCookieName) === code;
    }

    function removeLocaleChange() {
        sessionStorage.removeItem(sessionStorageKey);
    }

    function getLocaleChange() {
        return sessionStorage.getItem(sessionStorageKey);
    }

    function storeNeverShowNotice() {
        localStorage.setItem(neverShowNoticeKey, true);
    }

    function getNeverShowNotice() {
        return localStorage.getItem(neverShowNoticeKey) || false;
    }

    function trackGAEvent(action, locale) {
        if (win.ga) {
            var data = {
                category: 'Remember Language',
                action: action
            };

            if (locale) {
                data.label = locale;
            }
            mdn.analytics.trackEvent(data);
        }
    }

    if(win.sessionStorage && win.mdn.features.localStorage && !neverShowNotice) {
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
            var message = interpolate(text, {localeName: locale.name}, true);
            var button = '<button id="%s" type="button" data-locale="' + locale.code + '">%s</button> ';
            var yesButton = interpolate(button, ['locale-permanent-yes', gettext('Yes')]);
            var noButton = interpolate(button, ['locale-permanent-no', gettext('No')]);
            var neverButton = interpolate(button, ['locale-permanent-never', gettext('Never')]);
            var html = message + '<br>' + yesButton + noButton + neverButton;
            var notification = mdn.Notifier.growl(html, {closable: true, duration: 0});

            notification.question();
            removeLocaleChange();

            // Add event listener to the buttons
            $('#locale-permanent-yes').on('click', function() {
                var locale = this.dataset.locale;
                $.post('/i18n/setlang/', {language: locale})
                    .success(function() {
                        notification.close();
                    });

                // Track in GA
                // `locale` is actually locale code
                trackGAEvent('yes', locale);
            });

            $('#locale-permanent-no').on('click', function() {
                notification.close();
                // locale is a object. Track the locale code only
                trackGAEvent('no', locale.code);
            });

            $('#locale-permanent-never').on('click', function() {
                storeNeverShowNotice();
                notification.close();
                // locale is a object. Track the locale code only
                trackGAEvent('never', locale.code);
            });
        }
    }
})(window, document, jQuery);
