define(['intern'], function(intern) {

    var domain = intern.args.d || 'developer-local.allizom.org';
    var httpsAddress = 'https://' + domain + '/';
    var defaultLocale = 'en-US';

    return {

        // URLs
        domain: domain,
        url: httpsAddress,
        homepageUrl: httpsAddress + defaultLocale,
        demosHomepageUrl: httpsAddress + defaultLocale + '/demos',

        // Locales
        defaultLocale: defaultLocale,

        // Set the default browser dimentions
        defaultWidth: 1240,
        defaultHeight: 500,

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

        // Async testing in milliseconds
        testTimeout: 22000,
        asyncExecutionTimeout: 4000
    };

});
