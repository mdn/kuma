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

        // Important media queries
        mediaQueries: {
            smallDesktop: 1200,
            tablet: 1024,
            mobile: 768,
            smallMobile: 480
        },

        // Async testing in milliseconds
        testTimeout: 22000

    };

});
