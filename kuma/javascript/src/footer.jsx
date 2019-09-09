//@flow
import * as React from 'react';
import GithubIcon from './icons/social/github.svg';
import TwitterIcon from './icons/social/twitter.svg';
import InstagramIcon from './icons/social/instagram.svg';

import { getLocale, gettext } from './l10n.js';

export default function Footer() {
    const locale = getLocale();

    return (
        <footer id="nav-footer" className="nav-footer">
            <div className="center">
                <a href={`/${locale}/`} className="nav-footer-logo">
                    {gettext('MDN Web Docs')}
                </a>
                <div className="footer-group footer-group-mdn">
                    <h2 className="footer-title">MDN</h2>
                    <ul className="footer-list">
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
                        <li className="footer-social">
                            <a href="https://twitter.com/mozdevnet">
                                <TwitterIcon />
                            </a>
                        </li>
                        <li className="footer-social">
                            <a href="https://github.com/mdn/">
                                <GithubIcon />
                            </a>
                        </li>
                    </ul>
                </div>
                <a href="https://mozilla.org" className="nav-footer-mozilla">
                    {gettext('Mozilla')}
                </a>
                <div className="footer-group footer-group-mozilla">
                    <h2 className="footer-title">Mozilla</h2>
                    <ul className="footer-list">
                        <li>
                            <a href="https://www.mozilla.org/about/">
                                {gettext('About')}
                            </a>
                        </li>
                        <li>
                            <a href="https://www.mozilla.org/contact/">
                                {gettext('Contact Us')}
                            </a>
                        </li>
                        <li>
                            <a href="https://www.mozilla.org/firefox/?utm_source=developer.mozilla.org&utm_campaign=footer&utm_medium=referral">
                                Firefox
                            </a>
                        </li>
                        <li className="footer-social">
                            <a href="https://twitter.com/mozilla">
                                <TwitterIcon />
                            </a>
                        </li>
                        <li className="footer-social">
                            <a href="https://www.instagram.com/mozillagram/">
                                <InstagramIcon />
                            </a>
                        </li>
                    </ul>
                </div>
                <ul className="footer-tos">
                    <li>
                        <a href="https://www.mozilla.org/about/legal/terms/mozilla">
                            {gettext('Terms')}
                        </a>
                    </li>
                    <li>
                        <a href="https://www.mozilla.org/privacy/websites/">
                            {gettext('Privacy')}
                        </a>
                    </li>
                    <li>
                        <a href="https://www.mozilla.org/privacy/websites/#cookies">
                            {gettext('Cookies')}
                        </a>
                    </li>
                </ul>

                <div id="license" className="contentinfo">
                    <p>
                        &copy; 2005-{new Date().getFullYear()} Mozilla and
                        individual contributors.
                    </p>
                    <p>
                        Content is available under{' '}
                        <a href="/docs/MDN/About#Copyrights_and_licenses">
                            these licenses
                        </a>
                        .
                    </p>
                </div>
            </div>
        </footer>
    );
}
