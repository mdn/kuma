/**
 * The Router component defined in this file manages client side
 * navigation within the single-page app portions of MDN. Use the
 * Router with an array of Route objects that describe the kinds of
 * pages (for example document pages and search results pages) that
 * the router should handle.
 *
 * The Router will intercept clicks on links and form submissions
 * and if they are directed at URLs described by one of the routes, then
 * the Router will handle that navigation on the client side, using
 * methods of the Route object to parse the URL, fetch page data, and
 * get the page title and so on.
 *
 * The Router component also handles features related to client-side
 * navigation: it displays a loading animation, and submits data to
 * Google analytics.
 */
//@flow
import * as React from 'react';
import { useContext, useEffect, useRef, useState } from 'react';
import { css, keyframes } from '@emotion/core';

import type { ComponentType } from 'react';

import Route from './route.js';
import type { RouteParams, RouteData, RouteComponentProps } from './route.js';

import GAProvider from './ga-provider.jsx';
import {
    navigateStart,
    navigateFetchComplete,
    navigateRenderComplete
} from './perf.js';

// These are CSS animations for the loading bar
const slidein = keyframes`
  from { transform: translate(-90%, 0); }
  to { transform: translate(0, 0); }
`;
const throb = keyframes`
  from { opacity: 1.0; }
  to { opacity: 0.5; }
`;

// These are CSS styles for the loading bar
const styles = {
    loadingBar: css({
        position: 'fixed',
        display: 'none',
        height: 5,
        width: '100%',
        backgroundImage: 'linear-gradient(-271deg, #206584, #83d0f2)'
    }),
    loadingAnimation: css({
        display: 'block',
        animation: `${slidein} 0.5s, ${throb} 1s infinite alternate`
    })
};

// These are the props that we pass to the <Router> component
type RouterProps = {
    // These are the routes it can handle
    routes: Array<Route<RouteParams, RouteData>>,
    // The URL of the initial page to render
    initialURL: string,
    // The data for the initial page, if we have it.
    initialData: any
};

export default function Router({
    routes,
    initialURL,
    initialData
}: RouterProps) {
    /**
     * This type describes the basic state object that <Router> uses
     * to display the current page of the single page app.
     */
    type PageState = {
        // The URL of the page that is being displayed
        url: string,
        // The Route object that handles that URL
        route: Route<RouteParams, RouteData>,
        // The component to be used to render this page
        component: ?ComponentType<RouteComponentProps>,
        // Data extracted by Route.match() from the URL. The properties
        // of this object will become props of the component.
        params: ?RouteParams,
        // Data fetched asynchronously by the Route.fetch() function.
        // This value will be passed to the component as the data prop.
        data: ?RouteData
    };

    // Router state: this is the data we'll use below to render the page
    let [pageState: PageState, setPageState] = useState({
        url: null,
        route: null,
        component: null,
        params: null,
        data: null
    });

    // We also need to access the current page state from our event
    // handlers and from the route() function that they call. But the
    // event handlers are registered via useEffect() on the first
    // invocation of this component and so they are in a closure where
    // pageState is the variable defined on the very first invocation
    // always refers to its initial value. So we also need to define a
    // ref and keep pageStateRef.current up to date so that we can
    // access the current state.
    let pageStateRef = useRef(null);
    pageStateRef.current = pageState;

    // When loading is true we display a loading bar animation
    const [loading, setLoading] = useState(true);

    // Get the Google Analytics reporting function from our provider
    const ga = useContext(GAProvider.context);

    // Register one-time effects that run only on mount and set up
    // intercepting event handlers for client-side navigation via
    // links, form submissions and the back and forward handlers.
    // To keep the code clean, these effect function are defined below
    // after the rendering code and its return statement
    useEffect(interceptClickEvents, []);
    useEffect(interceptFormSubmissions, []);
    useEffect(handleBackAndForwardButtons, []);

    // These are effect functions that are run each time a page is
    // rendered with new (non-null) data. One effect deals with
    // analytics and the other stops the loading animation. Both
    // functions are defined at the bottom of the component.
    useEffect(recordAndReportAnalytics, [pageState.data]);
    useEffect(stopLoading, [pageState.data]);

    // When the page is first loaded, and this function is called for
    // the first time, we won't have a route defined in our state. In
    // this case, we use the initial URL and data that are passed to
    // us.  This route() is the key part of this Router component. It
    // figures out which route to use to render the page, uses the
    // match() and fetch() methods of that route to gather the
    // necessary data and then calls setPageState() which causes the
    // page to be re-rendered below.  After this first call to
    // route(), it is only called by the event handlers below when the
    // user clicks on links for submits forms or uses the back and
    // forward buttons in the browser.
    if (pageState.route === null) {
        route(initialURL, initialData);
    }

    // This is the code that actually renders and returns the React
    // components for the page. Note though that even though we're
    // returning here, the key route() function and the various effect
    // functions are defined below.
    //
    // If the page is loading we display a loading bar. On the very
    // first render, pageState.component will be undefined and we won't
    // render anything other than the loading bar. But the route()
    // call above will call setPageState() which will trigger a
    // re-render and we'll be called again with pageState.component
    // defined.
    return (
        <>
            <div
                css={[styles.loadingBar, loading && styles.loadingAnimation]}
            />
            {pageState.component && (
                <pageState.component
                    {...pageState.params}
                    data={pageState.data}
                />
            )}
        </>
    );

    /**
     * This is the main routing function. Pass it a url and it returns
     * a boolean. If it does not have any routes that can handle the url
     * it returns false. This tells the caller (in a click event handler
     * for example) that the user's click on a link cannot be handled on
     * the client side and that they need to let the browser handle it
     * via regular page load.
     *
     * If this function returns true, it means one of these things:
     *
     * 1) The specified URL is already displayed; no action is required
     *
     * 2) We have a route that can handle this url, we've called
     *    setPageState() and a re-render of the page is already
     *    pending.
     *
     * 3) We have a route that can handle this url. We're fetching
     *    data needed by the new page, but when that data arrives,
     *    we'll call setPageState() to rerender the page.
     *
     * In any of these cases, the return value of true means that the
     * url will be handled via client-side navigation and no further
     * action on the caller's part is required, except to call
     * preventDefault() on an event object to prevent the browser from
     * following a link or submitting a form.
     *
     * Normally this function is called with just one url argument.
     * But on the first call, if the initialData Router prop is set
     * we pass that value as the second argument so that we don't
     * need to make an asynchronous fetch. This second data argument
     * is important for server-side rendering.
     */
    function route(url: string, data: ?any = null): boolean {
        let pageState = pageStateRef.current;

        // If we are already displaying the requested URL, then
        // there is nothing that needs to be done and we can just return true.
        // This will prevent reloads when a page links to itself.
        if (url === pageState.url) {
            return true;
        }

        // Loop through the routes
        for (const route of routes) {
            // Check if each route knows how to handle the specified url
            let match = route.match(url);
            if (!match) {
                continue;
            }

            // We've found a route to handle our url.

            // Here is the new state data that we know about so far.
            // We still need to fetch some data for the page before we
            // can fully render it.
            let newPageState = {
                url: url,
                route: route,
                component: route.getComponent(),
                params: match,
                data: null
            };

            // If we were called with initial data, then we already
            // have all the pageState we need and can just call
            // setPageState() right away to cause the component to
            // rerender.  And in this case we're done.
            if (data) {
                newPageState.data = data;
                setPageState(newPageState);
                return true;
            }

            // Otherwise, we don't yet have the data we need to fully
            // render the page, and we're going to need to fetch it.
            // But we have a decision to make here. Do we call
            // setPageState() now to re-render the page with missing
            // data so that we can quickly get something on the
            // screen, or do we wait to call setPageState() until our
            // data is complete to minimize the updates the use
            // sees. I think the best answer is that if we're staying
            // within the same route (going from one document page to
            // another, for example) then we should wait and only
            // setPageState() when we have all the data. But if we're
            // switching routes (we did a search from a document page,
            // for example) then it is better to call setPageState()
            // right away to at least get the new search results
            // titlebar displayed even before the results themselves
            // are ready. Notice that this means we always call
            // setPageState() at this point for the first load.
            if (pageState.route !== newPageState.route) {
                // Note that we pass a copy of the newPageState object so
                // that when we call setPageState() again below with
                // the fetched data, the value will be different and
                // we'll get a re-render
                setPageState({ ...newPageState });
            }

            // In either case, we want to trigger the loading animation,
            // so we set that state variable now, too.
            setLoading(true);

            // Make a note of the time that we're starting this fetch
            // This should be within a millisecond of when the user
            // clicked on the link.
            navigateStart();

            // Use the fetch() function of the matching route to get
            // the data we need.
            route
                .fetch(match)
                .then(data => {
                    // When the data arrives:
                    // 1) Note how much time passed since navigateStart()
                    navigateFetchComplete();

                    // 2) Scroll back up to the top of the page
                    window.scrollTo(0, 0);

                    // 3) Ask the route what our page title is
                    // and set that title on the document, if it returns one
                    let title = route.getTitle(match, data);
                    if (title) {
                        document.title = title;
                    }

                    // 4: call setPageState() to cause the Router to
                    //    rerender and display the new page.
                    newPageState.data = data;
                    setPageState(newPageState);

                    // 5: When the page has finished rendering, the
                    //    stopLoading() and recordAndReportAnalytics()
                    //    effect functions below will be invoked to
                    //    finish up the client-side navigation process.
                })
                .catch(() => {
                    // If anything went wrong (such as a 404 when
                    // fetching data), we give up on client-side nav
                    // and just try loading the page. This may allow
                    // error recovery or will at least show the user
                    // a real 404 page.
                    window.location = url;
                });

            // Finally, return true to indicate that we found a
            // matching route and that data is being fetched (or
            // was already available)
            return true;
        }

        // None of our routes could handle the url, so return false
        return false;
    }

    // This is an effect function that runs once and register the
    // event listener that intercepts click events on links to
    // enable client-side navigation
    function interceptClickEvents() {
        // Flow complains if we don't verify this
        if (!document || !document.body) {
            return;
        }

        // A click event handler that triggers client-side navigation
        document.body.addEventListener('click', (e: MouseEvent) => {
            // If this is not a left click, or not a single click, or
            // if there are modifier keys, then this is not a simple
            // navigation that we can do on the client side, so do nothing.
            // Also if it was not a click on an HTMLElement, do nothing.
            if (
                e.button !== 0 ||
                e.detail > 1 ||
                e.altKey ||
                e.ctrlKey ||
                e.metaKey ||
                e.shiftKey ||
                !(e.target instanceof HTMLElement)
            ) {
                return;
            }

            // Find the closest enclosing <a> element
            let link = e.target.closest('a');

            // If the link is null, or is not actually an HTMLAnchorElement
            // or it does not have an href, or if the href includes
            // a hash, or if it is an off-site link, or if it has a target
            // attribute to open in another tab then we can't client
            // side navigate and should just return.
            if (
                !(link instanceof HTMLAnchorElement) ||
                !link.href ||
                link.hash ||
                link.target ||
                link.origin !== window.location.origin
            ) {
                return;
            }

            // Get the relative URL. This works because we checked the
            // origin and the hash above.
            let relativeURL = link.pathname + link.search;

            // Check whether we have any routes that know how to handle
            // this URL. If route() returns false, then we'll just return
            // and the browser will follow the link using a regular page
            // load.
            if (route(relativeURL)) {
                // If route() returns a true, then we found a router
                // that knows how to handle the link and a client side
                // navigation is now pending. We call preventDefault() so
                // that the browser will not actually follow the link.
                e.preventDefault();
                // And we record this new link in the browser history
                // so that the Back and Forward buttons will work correctly.
                history.pushState(relativeURL, '', relativeURL);
            }
        });
    }

    // This is an effect function that runs once and register the
    // event listener that intercepts form submissions (such as on the
    // MDN search box) to enable client side navigation.
    function interceptFormSubmissions() {
        // Flow complains if we don't verify this
        if (!document || !document.body) {
            return;
        }

        document.body.addEventListener('submit', (e: Event) => {
            // Do nothing if we can't find the form
            let form = e.target;
            if (!form || !(form instanceof HTMLFormElement)) {
                return;
            }

            // Don't client-side navigate for forms that POST or open new tabs
            if (form.method !== 'get' || form.target) {
                return;
            }

            // If the form action is a URL with a different origin then
            // we can't handle it with client-side navigation.
            if (!form.action.startsWith(window.location.origin)) {
                return;
            }

            // This is the form URL relative to the window origin
            let relativeURL = form.action.slice(window.location.origin.length);

            // Put together the query string and full url for this form
            let params = Array.from(form.querySelectorAll('[name]'))
                // $FlowFixMe: we kmow it has a name because of the query
                .map(e => `${e.name}=${e.value || ''}`)
                .join('&');
            relativeURL += `?${params}`;

            // See if we have a route that can handle it
            if (route(relativeURL)) {
                // If so, then stop the browser from submitting the form
                e.preventDefault();
                // And record this new URL in the browser history
                history.pushState(relativeURL, '', relativeURL);
            }
        });
    }

    // This is an effect function that runs once to register the
    // popstate event listener that makes the brower's Back and Forward
    // buttons work within our single-page application.
    function handleBackAndForwardButtons() {
        window.addEventListener('popstate', event => {
            // Every time we call pushState() or replaceState() we
            // pass the page URL as the state for the page. So if we
            // get a popstate event with state, we know that the state
            // is a URL and use route() to client-side navigate back
            // (or forward) to that page. We still have to check whether
            // state is defined, however, because popstate events are also
            // triggered when the user clicks on internal hash-only
            // links. And in that case we don't want to call route()
            if (event.state) {
                route(event.state);
            }
        });

        // In addition to the popstate handler, we also need to call
        // history.replaceState() for the current page that was just
        // loaded. Because that page was loaded by a regular browser load
        // it does not have state associated with it. But if we want the
        // browser to be able to go back to it by client-side navigation
        // we need to set its state.
        history.replaceState(initialURL, '', initialURL);
    }

    // This is an effect function that runs after a new page (with new
    // data) is rendered. It records performance metrics and submits data
    // to Google Analytics. This effect won't do anything if a new page
    // is rendered with null data: it will wait to be rendered after
    // the data arrives.
    function recordAndReportAnalytics() {
        let pageState = pageStateRef.current;
        if (!pageState.data) {
            return;
        }

        // Record the time since navigateStart() and send both the fetch
        // and render times to Google Analytics
        navigateRenderComplete(ga);

        // Set any Google Analytics variables specific to this route
        pageState.route.analyticsHook(ga, pageState.params, pageState.data);

        // Tell Google Analytics about this navigation.
        // We use 'dimension19' to mean client-side navigate
        // TODO: Need to ensure this is not set to yes on the initial page load.
        ga('set', 'dimension19', 'Yes');
        ga('send', 'pageview');
    }

    // This is an effect function that runs after a new page (with new
    // data) is rendered. It stops the loading animation if the data is ready.
    // If the page is re-rendered with null data, then this effect doesn't
    // do anything and waits until non-null data arrives.
    function stopLoading() {
        let pageState = pageStateRef.current;
        if (!pageState.data) {
            return;
        }

        // Client side navigation is typically so fast that the loading
        // animation might not even be noticed, so we artificially prolong
        // the effect with setTimeout()
        setTimeout(() => {
            setLoading(false);
        }, 200);
    }
}
