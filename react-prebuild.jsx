// @flow
import React from 'react';
import {renderToString} from 'react-dom/server';
import Logo from './kuma/javascript/src/Logo';

let stdinAccumulator = '';

process.stdin.on('data', input => {
    stdinAccumulator += input.toString();
});

process.stdin.on('end', () => {
    const locales = JSON.parse(stdinAccumulator);

    const result = Object.keys(locales).reduce((acc, locale) => ({
        [locale]: {
            Logo: renderToString(<Logo
                url={locales[locale].Logo.props.url}
            />),
        },
        ...acc
    }), {});

    console.log(JSON.stringify(result, null, 2))
});
