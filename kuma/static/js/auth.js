(function(win, doc, $) {
    'use strict';

    var $doc = $(doc);
    var $loginForm = $('#_persona_login');

    /*
        Async loading of the persona resource
    */
    (function() {
        var scriptUrl = $loginForm.data('persona-script');
        var personaElements = $('.wait-for-persona');

        if(personaElements.length && scriptUrl) {
            $.getScript(scriptUrl).done(function() {
                personaElements.removeClass('disabled');
            });
        }
    })();

    /*
        Persona Login via Django AllAuth
    */
    function initPersonaLogin(nextUrl, process) {
        // The actual form HTML code is within auth.html in the users app
        // The form must be populated with information provided gathered from
        // The link which triggered the login process
        $('#_persona_next_url').val(nextUrl || '');
        $('#_persona_process').val(process);

        // Start the Persona watcher
        navigator.id.watch({
            onlogin: function(assertion) {
                // TODO: Inject CSRF during normal page load
                $.get($loginForm.data('csrf-token-url')).then(function(token) {
                    $('#_persona_csrf_token').val(token);
                    $('#_persona_assertion').val(assertion);
                    $loginForm.trigger('submit');
                });
            }
        });

        // Launch Persona login window with the logo, return URL, etc.
        try {
            navigator.id.request($loginForm.data('request'));
        }
        catch(ex) { }
    }

    /*
        Open Auth Login Heading widget and standard login buttons
    */
    (function() {
        var $container = $('.oauth-login-container');
        var $options = $container.find('.oauth-login-options');
        var $picker = $container.find('.oauth-login-picker');
        var activeClass = 'active';
        var fadeSpeed = 300;

        $options.mozMenu({
            submenu: $picker,
            fadeInSpeed: fadeSpeed,
            fadeOutSpeed: fadeSpeed,
            onOpen: function() {
                $options.addClass(activeClass);
                $container.find('.submenu-close').attr('tabIndex', -1).appendTo($options);

            },
            onClose: function() {
                $container.find('.submenu-close').removeAttr('tabIndex').appendTo($container.find('.oauth-login-picker'));

                $options.removeClass(activeClass);
            }
        });
        $picker.find('ul').mozKeyboardNav();

        // Service click callback
        var trackingCallback = function() {
            // Track event of which was clicked
            var serviceUsed = $(this).data('service').toLowerCase(); // "Persona" or "GitHub"
            mdn.analytics.trackEvent({
                category: 'Authentication',
                action: 'Started sign-in',
                label: serviceUsed
            });

            // We use data-optimizely-hook and associated Optimizely element
            // targeting for most click goals, but if we are maintaining this
            // selector for Google Analytics anyway, we might as well use it.
            mdn.optimizely.push(['trackEvent', 'click-login-button-' + serviceUsed]);
        };

        // Track clicks on all login launching links
        $('.login-link').on('click', trackingCallback);

        // Ensure the login widget GitHub icon as clickable elements
        $container.find('.oauth-github').on('click', function(e) {
            e.stopPropagation();
            trackingCallback.apply(this, arguments);
            win.location = $(this).data('href');
        });

        // Ensure "launch-persona-login" elements launch the Persona window
        // Used for both login and connecting accounts, so don't assume login
        $(doc.body).on('click', '.launch-persona-login', function(e) {
            e.preventDefault();
            var $this = $(this);
            initPersonaLogin($this.data('next'), $this.data('process') || 'login');
        });
    })();

    // Track users successfully logging in
    $doc.on('mdn:login', function(e, service) {
        mdn.optimizely.push(['trackEvent', 'login']);
        mdn.optimizely.push(['trackEvent', 'login-' + service]);
        mdn.analytics.trackEvent({
            category: 'Authentication',
            action: 'Finished sign-in',
            label: service
        });
    });

    // Track users successfully logging out
    $doc.on('mdn:logout', function(e, service) {
        mdn.optimizely.push(['trackEvent', 'logout']);
        mdn.optimizely.push(['trackEvent', 'logout-' + service]);
        mdn.analytics.trackEvent({
            category: 'Authentication',
            action: 'Signed out',
            label: service
        });
    });

    /*
        Show notifications about account association status as part of the
        registration process.
    */
    if(win.mdn.features.localStorage) (function() {
        try {
            var $browserRegister = $('#browser_register');
            var matchKey = 'account-match-for';
            var matchCurrent = $browserRegister.data(matchKey);
            var matchStored = localStorage.getItem(matchKey);

            // The user is on the registration page and has been notified that
            // there is an MDN profile with a matching email address.
            if(matchCurrent && !matchStored) {
                localStorage.setItem(matchKey, matchCurrent);
            }

            // After seeing the notice, the user tried to sign in with a second
            // social account, but was again directed to the registration page.
            // This will happen if the second social account was also not
            // tied to an MDN profile.
            else if(!matchCurrent && matchStored && $browserRegister.length) {
                localStorage.removeItem(matchKey);
            }

            // After seeing the notice, the user took an action that resulted in
            // them landing on another page. Either the user abandoned the
            // registration process or the user tried to sign in with a second
            // social account and was successful. In either case, the
            // localStorage item should be immediately removed.
            else if(!matchCurrent && matchStored) {
                $doc.on('mdn:login', function(service) {
                    mdn.Notifier.growl('You can now use ' + matchStored + ' to sign in to this MDN profile.', { duration: 0, closable: true }).success();
                });
                localStorage.removeItem(matchKey);
            }

        }
        catch (e) {
            // Browser probably doesn't support localStorage
        }
    })();

    /*
        Fire off events when the user logs in and logs out.
    */
    if(win.mdn.features.localStorage) (function() {
        var serviceKey = 'login-service';
        var serviceStored = localStorage.getItem(serviceKey);
        var serviceCurrent = $(doc.body).data(serviceKey);

        try {

            // User just logged in
            if(serviceCurrent && !serviceStored) {
                localStorage.setItem(serviceKey, serviceCurrent);
                $doc.trigger('mdn:login', [ serviceCurrent ]);
            }

            // User just logged out
            else if(!serviceCurrent && serviceStored) {
                localStorage.removeItem(serviceKey);
                $doc.trigger('mdn:logout', [ serviceStored ]);
            }

        }
        catch (e) {
            // Browser probably doesn't support localStorage
        }
    })();

})(window, document, jQuery);
