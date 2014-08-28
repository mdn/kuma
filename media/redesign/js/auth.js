(function(win, doc, $) {
    'use strict';

    /*
        Persona Login via Django AllAuth
    */
    function initPersonaLogin(nextUrl, process) {
        // The actual form HTML code is within auth.html in the users app
        // The form must be populated with information provided gathered from
        // The link which triggered the login process

        var $loginForm = $('#_persona_login');
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
        var activeClass = 'active';
        var fadeSpeed = 300;

        // The options text is only hidden on tablets and lower, so only do the
        // JavaScript piece of the CSS is controlling text visibility
        var doMoveCloseButton = function() {
            return $container.find('.oauth-login-options-text').css('visibility') == 'hidden';
        };

        $options.mozMenu({
            fadeInSpeed: fadeSpeed,
            fadeOutSpeed: fadeSpeed,
            focusOnOpen: false,
            onOpen: function() {
                $options.addClass(activeClass);
                if(doMoveCloseButton()) {
                    $container.find('.submenu-close').attr('tabIndex', -1).appendTo($options);
                }
            },
            onClose: function() {
                if(doMoveCloseButton()) {
                    $container.find('.submenu-close').removeAttr('tabIndex').appendTo($container.find('.oauth-login-picker'));
                }
                $options.removeClass(activeClass);
            }
        });

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



    /*
        Track users successfully logging in and out
    */
    ('localStorage' in win) && (function() {
        var serviceKey = 'login-service';
        var serviceStored = localStorage.getItem(serviceKey);
        var serviceCurrent = $(doc.body).data(serviceKey);

        try {

            // User just logged in
            if(serviceCurrent && !serviceStored) {
                localStorage.setItem(serviceKey, serviceCurrent);

                mdn.optimizely.push(['trackEvent', 'login-' + serviceCurrent]);
                mdn.analytics.trackEvent({
                    category: 'Authentication',
                    action: 'Finished sign-in',
                    label: serviceCurrent
                });
            }

            // User just logged out
            else if(!serviceCurrent && serviceStored) {
                localStorage.removeItem(serviceKey);

                mdn.optimizely.push(['trackEvent', 'logout-' + serviceStored]);
                mdn.analytics.trackEvent({
                    category: 'Authentication',
                    action: 'Signed out',
                    label: serviceStored
                });
            }

        }
        catch (e) {
            // Browser probably doesn't support localStorage
        }
    })();



})(window, document, jQuery);
