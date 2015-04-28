// Returns a Page Object Model which will contain helper methods and
// required properties for individual tests

define(['base/lib/config', 'base/lib/login'], function(config, libLogin) {

    function POM(props) {
        // Mix in any properties or methods desired by usage
        if(props) {
            for(var prop in props) {
                this[prop] = props[prop];
            }
        }

        return this;
    }

    POM.prototype.init = function(remote, url) {
        this.remote = remote;
        this.url = url;

        return this;
    };

    // Setup the page.  This is a *must* for ensuring consistency in testing
    POM.prototype.setup = function() {
        var remote = this.remote;

        remote.setExecuteAsyncTimeout(config.asyncExecutionTimeout);

        // Go to the homepage, set the default size of the window
        return this.goTo().then(function() {
            return remote.setWindowSize(config.defaultWidth, config.defaultHeight);
        });
    };

    // Teardown the page.  This is a *must* for ensuring consistency in testing
    POM.prototype.teardown = function() {
        // Log out if the page is logged in
        return this.logout();
    };

    // Goes back to the page's URL
    POM.prototype.goTo = function(url) {
        return this.remote.get(url || this.url);
    };

    // Shortcut method to help with login
    POM.prototype.login = function(username, password) {
        var self = this;

        return libLogin.completePersonaLogin(self.remote, username, password).then(function() {
            self.loggedIn = true;
        });
    };

    // Shortcut method to log out
    POM.prototype.logout = function() {
        if(!this.loggedIn) return;

        return libLogin.completePersonaLogout(this.remote);
    };

    return POM;

});
