window.mdn.utils = {
    /**
     * Generate and returns a random string thanks to:
     * https://stackoverflow.com/questions/1349404/generate-random-string-characters-in-javascript
     * @param {Number} [strLength] - The length of the string to return
     * @return {String} a randomly generated string with a chracter count of `strLength`
     */
    randomString: function(strLength) {
        var length = strLength || 5;
        var possible =
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var text = '';

        for (var i = 0; i < length; i++) {
            text += possible.charAt(
                Math.floor(Math.random() * possible.length)
            );
        }

        return text;
    }
};
