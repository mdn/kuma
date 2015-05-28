// This file allows for overriding of certain config vars via the command line
// The local default config is assumed
define({
    mixinArgs: function(args, config) {

        var greps = [];

        // Take an argument with comma-separated value and apply it
        function checkAndParse(property, arg, callback) {
            if(arg) arg = arg.trim();
            if(!arg) return;

            config[property].length = 0;

            arg.trim().split(',').forEach(callback);
        }

        // Allow overriding of which browsers to run via a comma-separated string
        // ex: "firefox,chrome" or just "firefox"
        checkAndParse('environments', args.b, function(item) {
            config.environments.push({ browserName: item.trim() });
        });

        // Allow overriding of which test suites to run, so you can run one more more/*
        checkAndParse('functionalSuites', args.t, function(item) {
            config.functionalSuites.push('tests/' + item.trim());
        });

        // Set a username and password if present
        // If we weren't provided username and password, let's set a grep to avoid login tests
        if(args.u == undefined && args.p == undefined) {
            greps.push('requires-login');
            console.log('No username (-u) and password (-p) provided.  Tests requiring login will be skipped.');
        }

        // Set a document for wiki testing
        if(args.wd == undefined) {
            greps.push('requires-doc');
            console.log('No wiki document (-wd) provided.  Most wiki tests will be skipped.');
        }

        // Allow intrusive testing if specified (i.e. actually saving, editing generated documents)
        // DO NOT DO ON PRODUCTION
        if(args.destructive == true && config.productionDomain != config.domain) {
            greps.push('requires-destructive');
            console.log('No destructive permission provided.  Some wiki tests will be skipped.');
        }

        // Set the final GREP value
        args.grep = greps.length ? ('^(?!.*?\\[' + greps.join('|') + '\\])') : '';

        if(args.grep) {
            console.log('Command line arguments have forced a grep to skip tests:  ' + args.grep);
        }

        return config;
    }
});
