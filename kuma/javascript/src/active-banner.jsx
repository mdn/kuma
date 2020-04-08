/**
 * This file defines a React Banner component that renders a
 * call-to-action banner fixed to the bottom of the screen. The props
 * of the Banner component allow customization of the title,
 * description and button call-to-action text of the banner, as well
 * as the URL of the page that clicking on the call-to-action button
 * takes the user to. The Banner component is not exported,
 * however. Instead, we export an ActiveBanner component that pages should
 * use. It loops through an array of banner IDs for the first banner that is enabled by
 * Waffle and has not been dismissed by the user. If it finds such a
 * banner, it displays it with a <Banner>. Otherwise, if none of the
 * specified banners is enabled, or if all enabled banners have been
 * recently dismissed, then it displays nothing.
 *
 * When we want to change the set of banners displayed on MDN, we
 * can just edit the array of BannerProps objects in Banners() below.
 *
 * This file is a React port of the code in the following files:
 *
 *   kuma/banners/jinja2/banners/cta-banners.html
 *   kuma/banners/jinja2/banners/developer-needs.html
 *   kuma/static/js/components/banners/banners.js
 *   kuma/static/js/components/banners/utils/banners-event-util.js
 *   kuma/static/js/components/banners/utils/banners-state-util.js
 *
 * If you make changes in this file and also want those changes to be
 * reflected on the wiki site, you will need to edit those older files
 * as well.
 *
 * The reason that this React-based version of the banner feature is needed
 * is that in order to cache our pages in the CDN, we can't use waffle
 * flags in our HTML templates and instead have to modify all waffle-related
 * logic to query waffle flags obtained from the <UserProvider> context.
 *
 * This port removes the minimize feature from banners since it is
 * not used by the developer needs survey and seems unlikely to be
 * needed for future banners (it was part of the experimental payments
 * banner.)
 *
 * This ported component does not use CSS-in-JS, and depends on the
 * original banners stylesheet built from:
 *
 *    kuma/static/styles/components/banners/base.scss
 *
 * TODO: copy the styles from that stylesheet directly into this
 * component so that we only need to emit them (and the browser only
 * needs to parse them) when a banner will actually be rendered.
 *
 * @flow
 */
import * as React from 'react';
import { useContext, useState } from 'react';

import CloseIcon from './icons/close.svg';
import { getLocale, gettext } from './l10n.js';
import UserProvider from './user-provider.jsx';

// Set a localStorage key with a timestamp the specified number of
// days into the future. When the user dismisses a banner we use this
// to prevent the redisplay of the banner for a while.
function setEmbargoed(id, days) {
    try {
        let key = `banner.${id}.embargoed_until`;
        localStorage.setItem(
            key,
            String(Date.now() + Math.round(days * 24 * 60 * 60 * 1000))
        );
    } catch (e) {
        // If localStorage is not supported, then embargos are not supported.
    }
}

// See whether the specified id was passed to setEmbargoed() fewer than the
// specified number of days ago. We check this before displaying a banner
// so a user does not see a banner they recently dismissed.
function isEmbargoed(id) {
    try {
        let key = `banner.${id}.embargoed_until`;
        let value = localStorage.getItem(key);
        // If it is not set, then the banner has never been dismissed
        if (!value) {
            return false;
        }
        // The value from localStorage is a timestamp that we compare to
        // the current time
        if (parseInt(value) > Date.now()) {
            // If the timestamp is in the future then the banner has been
            // dismissed and the embargo has not yet expired.
            return true;
        } else {
            // Otherwise, the banner was dismissed, but the embargo has
            // expired and we can show it again.
            localStorage.removeItem(key);
            return false;
        }
    } catch (e) {
        // If localStorage is not supported, then the embargo feature
        // just won't work
        return false;
    }
}

// The <Banner> component displays a simple call-to-action banner at
// the bottom of the window. The following props allow it to be customized.
//
// TODO: we should probably make the image and maybe the background of
// the banner configurable through props like these. For now, however,
// that is hardcoded into the stylesheet.
export type BannerProps = {
    // A unique string associated with this banner. It must match the
    // name of the waffle flag that controls the banner, and is also
    // used as part of a localStorage key.
    id: string,
    // class name used on main banner container. Exclusively used
    // for styling purposes.
    classname: string,
    // The banner title. e.g. "MDN Survey"
    title: string,
    // The banner description. e.g. "Help us understand the top 10 needs..."
    // Could also be a React Element such as that returned by `<Interpolated />`
    copy: Object | string,
    // The call to action button text. e.g. "Take the survey"
    cta: string,
    // The URL of the page to open when the button is clicked
    url: string,
    // An optional property. If present, it should be set to true to indicate
    // that this banner is to be shown to authenticated users only
    authenticated?: boolean,
    // An optional property. If present, it specifies the number of days
    // for which a dismissed banner will not be shown. If omitted, the
    // default is 5 days.
    embargoDays?: number,
    // An optional property. If present, it should be set to true to indicate
    // that the main cta link should open in a new window
    newWindow?: boolean,
};

function Banner(props: BannerProps) {
    const [isDismissed, setDismissed] = useState(false);
    const containerClassNames = `${props.classname} mdn-cta-container cta-background-linear`;

    if (isDismissed) {
        return null;
    }

    return (
        <div className={containerClassNames}>
            <div id="mdn-cta-content" className="mdn-cta-content">
                <div id={props.id} className="mdn-cta-content-container">
                    <h2 className="mdn-cta-title slab-text">{props.title}</h2>
                    <p className="mdn-cta-copy">{props.copy}</p>
                </div>
                <p className="mdn-cta-button-container">
                    <a
                        href={props.url}
                        className="mdn-cta-button"
                        target={props.newWindow && '_blank'}
                        rel={props.newWindow && 'noopener noreferrer'}
                    >
                        {props.cta}
                    </a>
                </p>
            </div>
            <div className="mdn-cta-controls">
                <button
                    type="button"
                    id="mdn-cta-close"
                    className="mdn-cta-close"
                    aria-label={gettext('Close banner')}
                    onClick={() => {
                        setDismissed(true);
                        setEmbargoed(props.id, props.embargoDays || 5);
                    }}
                >
                    <CloseIcon className="icon icon-close" />
                </button>
            </div>
        </div>
    );
}

export const DEVELOPER_NEEDS_ID = 'developer_needs';
export const SUBSCRIPTION_ID = 'subscription_banner';

export default function ActiveBanner() {
    const userData = useContext(UserProvider.context);
    const locale = getLocale();

    if (!userData || !userData.waffle.flags) {
        return null;
    }

    for (const id in userData.waffle.flags) {
        if (!userData.waffle.flags[id] || isEmbargoed(id)) {
            continue;
        }

        // The Subscription banner is special. It should not be displayed
        // if the user has a truthy `isSubscriber`.
        if (id === SUBSCRIPTION_ID) {
            if (userData.isSubscriber) {
                // This user will NOT get this banner.
                return true;
            }
        }

        switch (id) {
            case DEVELOPER_NEEDS_ID:
                return (
                    <Banner
                        id={id}
                        classname="developer-needs"
                        title={gettext('MDN Survey')}
                        copy={gettext(
                            'Help us understand the top 10 needs of Web developers and designers.'
                        )}
                        cta={gettext('Take the survey')}
                        url={
                            'https://qsurvey.mozilla.com/s3/Developer-Needs-Assessment-2019'
                        }
                        newWindow
                    />
                );

            case SUBSCRIPTION_ID:
                if (!userData.isAuthenticated) {
                    return null;
                }

                return (
                    <Banner
                        id={id}
                        classname="mdn-subscriptions"
                        title={gettext('Become a monthly supporter')}
                        // do not hardcode dollar amount, use CONTRIBUTION_AMOUNT_USD
                        // https://github.com/mdn/kuma/issues/6654
                        copy={gettext(
                            'Support MDN with a $5 monthly subscription'
                        )}
                        cta={gettext('Learn more')}
                        url={`/${locale}/payments/`}
                        embargoDays={7}
                    />
                );
        }
    }

    // No banner found in the waffle flags, so we have nothing to render
    return null;
}
