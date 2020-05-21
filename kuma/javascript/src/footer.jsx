//@flow
import * as React from 'react';
import GithubIcon from './icons/social/github.svg';
import TwitterIcon from './icons/social/twitter.svg';
import InstagramIcon from './icons/social/instagram.svg';

import { getLocale, gettext } from './l10n.js';

export default function Footer() {
    const locale = getLocale();

    return (
        <footer id="nav-footer" className="nav-footer" data-testid="footer">
            <div className="content-container">
                <a href={`/${locale}/`} className="nav-footer-logo">
                    {gettext('MDN Web Docs')}
                </a>
                <ul className="link-list-mdn">
                    <li>
                        <a href={`/${locale}/docs/Web`}>
                            {gettext('Web Technologies')}
                        </a>
                    </li>
                    <li>
                        <a href={`/${locale}/docs/Learn`}>
                            {gettext('Learn Web Development')}
                        </a>
                    </li>
                    <li>
                        <a href={`/${locale}/docs/MDN/About`}>
                            {gettext('About MDN')}
                        </a>
                    </li>
                    <li>
                        <a href={`/${locale}/docs/MDN/Feedback`}>
                            {gettext('Feedback')}
                        </a>
                    </li>
                </ul>

                <ul className="link-list-moz">
                    <li>
                        <a
                            href="https://www.mozilla.org/about/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {gettext('About')}
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://shop.spreadshirt.com/mdn-store/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            MDN Web Docs Store
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://www.mozilla.org/contact/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {gettext('Contact Us')}
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://www.mozilla.org/firefox/?utm_source=developer.mozilla.org&utm_campaign=footer&utm_medium=referral"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Firefox
                        </a>
                    </li>
                </ul>

                <div className="social social-mdn">
                    <h4>{gettext('MDN')}</h4>
                    <ul>
                        <li>
                            <a
                                href="https://twitter.com/mozdevnet"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <TwitterIcon />
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://github.com/mdn/"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <GithubIcon />
                            </a>
                        </li>
                    </ul>
                </div>

                <div className="social social-moz">
                    <h4>{gettext('Mozilla')}</h4>
                    <ul>
                        <li>
                            <a
                                href="https://twitter.com/mozilla"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <TwitterIcon />
                            </a>
                        </li>
                        <li>
                            <a
                                href="https://www.instagram.com/mozillagram/"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                <InstagramIcon />
                            </a>
                        </li>
                    </ul>
                </div>

                <p id="license" className="footer-license">
                    &copy; 2005-{new Date().getFullYear()} Mozilla and
                    individual contributors. Content is available under{' '}
                    <a href="/docs/MDN/About#Copyrights_and_licenses">
                        these licenses
                    </a>
                    .
                </p>

                <ul className="footer-legal">
                    <li>
                        <a
                            href="https://www.mozilla.org/about/legal/terms/mozilla"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {gettext('Terms')}
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://www.mozilla.org/privacy/websites/"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {gettext('Privacy')}
                        </a>
                    </li>
                    <li>
                        <a
                            href="https://www.mozilla.org/privacy/websites/#cookies"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {gettext('Cookies')}
                        </a>
                    </li>
                </ul>
            </div>
        </footer>
    );
}
