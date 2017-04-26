module.exports = {
    "env": {
        "browser": true,
        "es6": true,
        "jquery": true,
        "jasmine": true
    },
    "extends": "eslint:recommended",
    "rules": {
        "no-global-assign": 1,
        "indent": [
            1,
            4
        ],
        "linebreak-style": [
            1,
            "unix"
        ],
        "camelcase": 1,
        "indent": 1,
        "no-cond-assign": 1,
        "no-console": 1,
        "no-empty": 1,
        "no-extra-semi": 1,
        "no-fallthrough": 1,
        "no-redeclare": 1,
        "no-undef": 1,
        "no-unused-vars": 1,
        "quotes": [
            1,
            "single"
        ],
        "semi": [
            1,
            "always"
        ],
        "curly": [
            1,
            "all"
        ],
        "camelcase": [
            1,
            {
                "properties": "always"
            }
        ],
        "eqeqeq": [
            1,
            "smart"
        ],
        "one-var-declaration-per-line": [
            1,
            "always"
        ],
        "new-cap": 1
    },
    "globals": {
        "CKEDITOR": true,
        "FontFaceObserver": true,
        "ga": true,
        "gettext": true,
        "interpolate": true,
        "mdn": true,
        "Mozilla": true
    }
};
