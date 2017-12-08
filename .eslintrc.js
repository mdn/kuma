module.exports = {
    'env': {
        'browser': true,
        'jquery': true
    },
    'extends': 'eslint:recommended',
    'rules': {
        'no-global-assign': 'error',
        'indent': [
            'error',
            4,
            {SwitchCase: 1}
        ],
        'linebreak-style': [
            'error',
            'unix'
        ],
        'no-cond-assign': 'error',
        'no-console': ['error', {
            'allow': ['error', 'info']
        }],
        'no-empty': 'error',
        'no-extra-semi': 'error',
        'no-fallthrough': 'error',
        'no-redeclare': 'error',
        'no-undef': 'error',
        'no-unused-vars': 'error',
        'quotes': [
            'error',
            'single'
        ],
        'semi': [
            'error',
            'always'
        ],
        'curly': [
            'error',
            'all'
        ],
        'camelcase': [
            'error',
            {
                'properties': 'always'
            }
        ],
        'eqeqeq': [
            'error',
            'smart'
        ],
        'one-var-declaration-per-line': [
            'error',
            'always'
        ],
        'new-cap': 'error'
    },
    'globals': {
        'CKEDITOR': true,
        'FontFaceObserver': true,
        'ga': true,
        'gettext': true,
        'interpolate': true,
        'mdn': true,
        'Mozilla': true,
        'waffle': true,
        'Prism': true,
        'Promise': true
    }
};
