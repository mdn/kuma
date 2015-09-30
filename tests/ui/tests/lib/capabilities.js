define({

    getBrowserName: function(remote) {
        return remote.session.capabilities.browserName.toLowerCase();
    }

});
