// This file allows for overriding of certain config vars via the command line
// The local default config is assumed
define({
    mixinArgs: function(args, config) {

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

        return config;
    }
});
