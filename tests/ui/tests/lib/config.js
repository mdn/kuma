define(['intern'], function(intern) {

    var domain = intern.args.d || 'developer.allizom.org';
    var httpsAddress = 'https://' + domain + '/';
    var defaultLocale = 'en-US';

    return {
        // URLs
        domain: domain,
        url: httpsAddress,
        homepageUrl: httpsAddress + defaultLocale,
        productionDomain: 'developer.mozilla.org',

        // Locales
        defaultLocale: defaultLocale,

        // Set the default browser dimentions
        defaultWidth: 1240,
        defaultHeight: 800,

        // Important media queries
        mediaQueries: {
            smallDesktop: 1200,
            tablet: 1024,
            mobile: 768,
            smallMobile: 480
        },

        // Credentials
        personaUsername: intern.args.u || '',
        personaPassword: intern.args.p || '',

        // Testing timeouts in milliseconds
        // Set high so that remote runners like BrowserStack can complete in case of slow site
        testTimeout: 60000,

        // Wiki-specific
        wikiDocumentSlug: intern.args.wd || ''
    };

});
