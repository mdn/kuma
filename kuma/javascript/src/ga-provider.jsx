// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

export type GAFunction = (...any) => void;

export const CATEGORY_MONTHLY_PAYMENTS = 'monthly payments';

const GA_QUERY_KEY = 'ga';

const QUERY_PARAM_GA_DATA = {
    'subscription-success': {
        hitType: 'event',
        eventCategory: CATEGORY_MONTHLY_PAYMENTS,
        eventAction: 'successful subscription',
        eventLabel: 'subscription-landing-page',
    },
    'banner-cta': {
        hitType: 'event',
        eventCategory: CATEGORY_MONTHLY_PAYMENTS,
        eventAction: 'subscribe intent',
        eventLabel: 'banner',
    },
};

export function gaQuery(id: $Keys<typeof QUERY_PARAM_GA_DATA>) {
    return GA_QUERY_KEY + '=' + id;
}

function ga(...args) {
    if (typeof window === 'object' && typeof window.ga === 'function') {
        window.ga(...args);
    }
}

const context = React.createContext<GAFunction>(ga);

/**
 * If we're running in the browser (not being server-side rendered)
 * and if the HTML document includes the Google Analytics snippet that
 * defines the ga() function, then this provider component makes that
 * ga() function available to any component via:
 *
 *    let ga = useContext(GAProvider.context)
 *
 * If we're not in a browser or if google analytics is not enabled,
 * then we provide a dummy function that ignores its arguments and
 * does nothing.  The idea is that components can always safely call
 * the function provided by this component.
 */
export default function GAProvider(props: {
    children: React.Node,
}): React.Node {
    /**
     * Checks for the existence of the analytics parameter in the URL query,
     * and sends events for every present parameter for which we have associated
     * analytics data.
     */
    useEffect(() => {
        const analyticIds = new URLSearchParams(
            window.location.search.substr(1)
        )
            .getAll(GA_QUERY_KEY)
            .filter((id) => id in QUERY_PARAM_GA_DATA);

        for (const id of analyticIds) {
            ga('send', QUERY_PARAM_GA_DATA[id]);
        }
    }, []);

    return <context.Provider value={ga}>{props.children}</context.Provider>;
}

// This is a custom hook to return the GA client id. It returns the
// emtpy string until (and unless) it can determine that id from the GA object.
function useClientId() {
    const [clientId, setClientId] = useState<string>('');
    const ga = useContext(GAProvider.context);
    useEffect(() => {
        ga((tracker) => {
            setClientId(tracker.get('clientId'));
        });
    }, [ga]);

    return clientId;
}

// Export both the context object and the custom hook as properties
// of the GAProvider component
GAProvider.context = context;
GAProvider.useClientId = useClientId;
