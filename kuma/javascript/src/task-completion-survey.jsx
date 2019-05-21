// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';
import css from '@emotion/css';

import CloseIcon from './icons/close.svg';
import DocumentProvider from './document-provider.jsx';
import GAProvider from './ga-provider.jsx';
import { getLocale, gettext } from './l10n.js';
import UserProvider from './user-provider.jsx';

const styles = {
    notification: css({
        position: 'fixed',
        display: 'flex',
        flexDirection: 'row',
        top: 15,
        right: 15,
        width: 300,
        padding: 15,
        paddingRight: 8,
        zIndex: 999999,
        fontSize: 16,
        backgroundColor: '#e4f0f5',
        color: '#333',
        border: 'solid #3d7e9a 2px',
        borderRadius: 2,
        boxShadow: '3px 3px 5px rgba(0, 0, 0, 0.25)'
    }),
    dismissButton: css({
        alignSelf: 'start',
        padding: 0,
        borderWidth: 0,
        backgroundColor: 'inherit'
    }),
    dismissIcon: css({
        height: 18
    })
};

// This is the name of the waffle flag that controls this notification
const WAFFLE_FLAG = 'sg_task_completion';

// This is the name of a localStorage property we use to prevent the
// display of the notification to someone who has dismissed it or
// responded to it within the last month
const EMBARGO_TIMESTAMP = 'taskTracker';

// This is how long the embargo lasts
const EMBARGO_LENGTH = 1000 * 60 * 60 * 24 * 32; // 32 days

// If the user dismisses or responds to the survey, then we call this
// function to set the embargo timestamp. During this embargo period,
// the notification will not be shown again to the user.
function embargo() {
    try {
        localStorage.setItem(
            EMBARGO_TIMESTAMP,
            String(Date.now() + EMBARGO_LENGTH)
        );
    } catch (e) {
        // Silently ignore localStorage failures
    }
}

// This function returns true if the embargo timestamp is set in
// local storage, and the embargo period has not yet elapsed.
function isEmbargoed() {
    try {
        return (
            !!localStorage[EMBARGO_TIMESTAMP] &&
            parseInt(localStorage[EMBARGO_TIMESTAMP]) > Date.now()
        );
    } catch (e) {
        // If localStorage is not working then we'll always behave
        // as if the notification is embargoed, and the user will never
        // see anything. (This is presumably better than possibly annoying
        // users by showing it to them too frequently.)
        return true;
    }
}

export default function TaskCompletionSurvey() {
    const documentData = useContext(DocumentProvider.context);
    const ga = useContext(GAProvider.context);
    const clientId = GAProvider.useClientId();
    const userData = useContext(UserProvider.context);
    const [isDismissed, setDismissed] = useState(false);
    const locale = getLocale();

    // Show the notification if...
    const shouldShow =
        !!userData && // we have user data
        !!userData.waffle.flags[WAFFLE_FLAG] && // and the waffle flag is set
        !isDismissed && // and the user has not dismissed it
        !isEmbargoed(); // and it is not embargoed

    useEffect(() => {
        if (shouldShow) {
            // If we are showing the notification and asking the user to
            // complete the survey, then tell Google Analytics about it.
            // GA dimension14 is "Saw Survey Gizmo Task Completion survey".
            //
            // Note that since this code runs in useEffect() it only
            // runs once each time that shouldShow becomes
            // true. So if the notification follows the user across
            // multiple client-side navigations, for example, we won't
            // send these GA events each time we re-render.
            ga('set', 'dimension14', 'Yes');
            ga('send', {
                hitType: 'event',
                eventCategory: 'survey',
                eventAction: 'prompt',
                eventLabel: '',
                eventValue: 'impression',
                nonInteraction: true
            });
        }
    }, [shouldShow]);

    // If we're not going to show anything, we can just return now.
    if (!shouldShow) {
        return null;
    }

    // Construct the survey URL.
    let surveyURL = 'https://www.surveygizmo.com/s3/2980494/do-or-do-not';
    // Use a future timestamp because we're asking the user to open
    // the survey now and fill it out later.  20 minutes is a guess.
    surveyURL += `?t=${Date.now() + 1000 * 60 * 20}`;
    if (documentData) {
        surveyURL += `&p=${encodeURIComponent(
            `/${locale}/docs/${documentData.slug}`
        )}`;
    }
    // When we are first displayed we won't have the GA client ID, but the
    // useClientId() hook function above will get it and we'll be re-rendered
    // which will update the URL to add the client id.
    if (clientId) {
        surveyURL += `&c=${encodeURIComponent(clientId)}`;
    }

    // Called when the user clicks the X icon or the survey link
    function dismiss() {
        // When the notification is dismissed ensure that the user
        // won't see it again for a period of time.
        embargo();
        // And now set the state variable that actually hides the notification.
        setDismissed(true);
    }

    // Called when the user clicks the survey link
    function recordAndDismiss() {
        // If the user clicks on the survey link, let Google Analytics know.
        ga('send', {
            hitType: 'event',
            eventCategory: 'survey',
            eventAction: 'prompt',
            eventLabel: '',
            eventValue: 'participate',
            nonInteraction: false
        });
        // Since they opened the survey, we can dismiss the notification
        dismiss();
    }

    return (
        <div css={styles.notification}>
            <div>
                {gettext('Would you answer 4 questions for us?')}{' '}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href={surveyURL}
                    onClick={recordAndDismiss}
                >
                    {gettext('Open the survey in a new tab')}
                </a>{' '}
                {gettext(
                    'and fill it out when you are done on the site. Thanks!'
                )}
            </div>
            <button
                css={styles.dismissButton}
                onClick={dismiss}
                aria-label={gettext('Dismiss')}
            >
                <CloseIcon css={styles.dismissIcon} />
            </button>
        </div>
    );
}
