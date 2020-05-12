module.exports = {
    env: {
        browser: true,
        es6: true,
        'jest/globals': true,
        jquery: true,
        node: true,
    },
    parser: 'babel-eslint',
    parserOptions: {
        ecmaVersion: 6,
    },
    plugins: [
        'jest',
        'jest-dom',
        'flowtype',
        'import',
        'jsx-a11y',
        'react-hooks',
        'testing-library',
    ],
    extends: [
        'eslint:recommended',
        'plugin:import/errors',
        'plugin:flowtype/recommended',
        'plugin:jsx-a11y/recommended',
        'plugin:jest-dom/recommended',
        'plugin:testing-library/recommended',
        'prettier',
    ],
    rules: {
        'no-global-assign': 'error',
        indent: ['error', 4, { SwitchCase: 1 }],
        'linebreak-style': ['error', 'unix'],
        'no-cond-assign': 'error',
        'no-console': [
            'error',
            {
                allow: ['error', 'info'],
            },
        ],
        'no-empty': 'error',
        'no-extra-semi': 'error',
        'no-fallthrough': 'error',
        'no-redeclare': 'error',
        'no-undef': 'error',
        'no-unused-vars': 'error',
        quotes: ['error', 'single'],
        semi: ['error', 'always'],
        curly: ['error', 'all'],
        camelcase: [
            'error',
            {
                properties: 'always',
            },
        ],
        eqeqeq: ['error', 'smart'],
        'one-var-declaration-per-line': ['error', 'always'],
        'new-cap': 'error',
        'react-hooks/rules-of-hooks': 'error',
        'react-hooks/exhaustive-deps': 'warn',
    },
    globals: {
        CKEDITOR: true,
        ga: true,
        gettext: true,
        interpolate: true,
        mdn: true,
        Mozilla: true,
        waffle: true,
        Prism: true,
        Promise: true,
    },
};
