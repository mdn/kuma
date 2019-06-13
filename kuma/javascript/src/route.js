// @flow
/* eslint-disable no-unused-vars */ // Because of abstract method params

import type { ComponentType } from 'react';

import type { GAFunction } from './ga-provider.jsx';

export type RouteParams = { [string]: any };
export type RouteData = any;
export type RouteComponentProps = RouteParams & { data: RouteData };

/**
 * A Route object describes one kind of page that we know how to handle
 * as part of the MDN single-page app. Currently ./routes.js defines two
 * routes: one for document pages and one for search results.
 * TODO: Update the comments in this file now that we've switched to a class.
 */
export default class Route<Params: RouteParams, Data: RouteData> {
    // The getComponent() method of a Route returns the React
    // component that will be used to render the page for this
    // route. This component will be invoked with the RouteData
    // returned by match() and the data asynchronously returned by
    // fetch() as its props:
    //
    //   <component {...params} data={data}/>
    //
    // The component's prop types should match the type declarations for
    // the Params and Data properties of the subclass
    //
    // This method is abstrct: all Route subclasses must override it.
    //
    getComponent(): ComponentType<Params & { data: Data }> {
        throw new Error('All Route subclasses must override getComponent()');
    }

    // The match() method of a route takes a url (or just a path) as
    // its input and returns null if it can't handle that URL, or a
    // Params object if it can handle the url. The Params object
    // typically consists of properties (such as locale and slug) that
    // are extracted from the URL.
    //
    // This method is abstrct: all Route subclasses must override it.
    //
    match(url: string): ?Params {
        throw new Error('All Route subclasses must override match()');
    }

    // The fetch() method of a route takes a Params object as its
    // input and returns a Promise for an asynchronous fetch for data
    // needed to render the page. Route types that don't need to fetch
    // any data can just inherit this method which synchronously
    // returns null, indicating that nothing needs fetching.
    //
    // TODO: update Router to handle the null return case
    //
    fetch(params: Params): ?Promise<Data> {
        return null;
    }

    // After match() and fetch() are called, and the Promise returned
    // by fetch has resolved, the router will call this function with
    // the matched params and fetched data in order to get a title for
    // the page it is about to render. If the method returns a truthy
    // value, it will be set on document.title. Routes that implement
    // their own title handling can just inherit this implementation
    // and the Router will not set any title.
    getTitle(params: Params, data: Data): ?string {
        return null;
    }

    // After match() and fetch() are called, and the Promise returned
    // by fetch has resolved, the router will call this function with
    // the matched params and fetched data in order give the route an
    // opportunity to set Google Analytics variables (with `ga("set",
    // ...)`) before the router calls ga("send", "pageview"). This default
    // implementation does nothing.
    analyticsHook(
        ga: GAFunction,
        matchedData: Params,
        fetchedData: Data
    ): void {}
}
