//@flow
import React from 'react';
import { css } from '@emotion/core';
import styled from '@emotion/styled';

import Login from './login.jsx';
import Logo from './logo.jsx';
import Dropdown from './dropdown.jsx';
import Search from './search.jsx';
import gettext from '../gettext.js';

const styles = {
    headerRow: css({ borderTop: '5px solid #83d0f2' })
};

const Row = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
`;

const Spring = styled.div`
    flex: 1 1 0px;
`;

const Strut = styled.div(props => ({
    flexGrow: 0,
    flexShrink: 0,
    flexBasis: props.width
}));

// TODO: the labels all need to be localized
const menus = [
    {
        label: 'Technologies',
        items: [
            { url: 'Web/HTML', label: 'HTML' },
            { url: 'Web/CSS', label: 'CSS' },
            { url: 'Web/JavaScript', label: 'JavaScript' },
            { url: 'Web/Guide/Graphics', label: 'Graphics' },
            { url: 'Web/HTTP', label: 'HTTP' },
            { url: 'Web/API', label: 'APIs / DOM' },
            {
                url: 'Mozilla/Add-ons/WebExtensions',
                label: 'Browser Extensions'
            },
            { url: 'Web/MathML', label: 'MathML' }
        ]
    },
    {
        label: 'References & Guides',
        items: [
            { url: 'Learn', label: 'Learn web development' },
            { url: 'Web/Tutorials', label: 'Tutorials' },
            { url: 'Web/Reference', label: 'References' },
            { url: 'Web/Guide', label: 'Developer Guides' },
            { url: 'Web/Accessibility', label: 'Accessibility' },
            { url: 'Games', label: 'Game development' },
            { url: 'Web', label: '...more docs' }
        ]
    },
    {
        label: 'Feedback',
        items: [
            {
                url: 'https://support.mozilla.org/',
                label: 'Get Firefox help',
                external: true
            },
            {
                url: 'https://stackoverflow.com/',
                label: 'Get web development help',
                external: true
            },
            { url: 'MDN/Community', label: 'Join the MDN community' },
            {
                label: 'Report a content problem',
                external: true,
                url: `https://github.com/mdn/sprints/issues/new?template=issue-template.md&projects=mdn/sprints/2&labels=user-report&title=${encodeURIComponent(
                    window.location
                )}`
            },
            {
                label: 'Report a bug',
                external: true,
                url: 'https://bugzilla.mozilla.org/form.mdn'
            }
        ]
    }
];

function fixurl(url) {
    if (url.startsWith('https://')) {
        return url;
    } else {
        let locale = window.location.pathname.split('/')[1];
        return `/${locale}/docs/${url}`;
    }
}

const HOME_URL =
    window && window.location
        ? `${window.location.protocol}//${window.location.host}/${
              window.location.pathname.split('/')[1]
          }/`
        : 'https://developer.moilla.org/en-US/';

export default function Header(): React.Node {
    return (
        <Row css={styles.headerRow}>
            <Logo url={HOME_URL} />
            <Strut width={4} />
            {menus.map((m, index) => (
                <Dropdown label={gettext(m.label)} key={index}>
                    {m.items.map((item, index) => (
                        <li key={index}>
                            {item.external ? (
                                <a
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    href={fixurl(item.url)}
                                >
                                    {gettext(item.label)} &#x1f310;
                                </a>
                            ) : (
                                <a href={fixurl(item.url)}>
                                    {gettext(item.label)}
                                </a>
                            )}
                        </li>
                    ))}
                </Dropdown>
            ))}
            <Spring />
            <Search />
            {/* search box here */}
            <Strut width={15} />
            <Login />
            <Strut width={15} />
        </Row>
    );
}
