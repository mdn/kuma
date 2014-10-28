define(['intern'], function(intern) {

    return {
        // Persona credentials for logging in
        personaUsername: intern.args.u || '',
        personaPassword: intern.args.p || ''
    };

});
