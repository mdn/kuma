//@flow
import * as React from 'react';
import { css } from '@emotion/core';

import gettext from '../gettext.js';
import GithubLogo from './github-logo.svg';

const PATHNAME = window && window.location ? window.location.pathname : '/';

const strings = {
    signin: gettext('Sign in')
};

const styles = {
    a: css({
        fontSize: 18,
        fontWeight: 'bold',
        color: 'black',
        textDecoration: 'none',
        ':hover': { textDecoration: 'none' }
    }),
    icon: css({ verticalAlign: -6 })
};

export default function Login(): React.Node {
    return (
        <a
            href={`/users/github/login/?next=${PATHNAME}`}
            data-service="GitHub"
            rel="nofollow"
            css={styles.a}
        >
            {strings.signin} <GithubLogo css={styles.icon} />
        </a>
    );
}
