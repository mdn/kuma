/* This Source Code Form is subject to the terms of the Mozilla Public
* License, v. 2.0. If a copy of the MPL was not distributed with this
* file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// create namespace
if (typeof Mozilla === 'undefined') {
    var Mozilla = {};
}

/**
 * Traffic Cop traffic redirector for A/B/x testing
 *
 * Example usage:
 *
 * var cop = new Mozilla.TrafficCop({
 *     id: 'exp_firefox_new_all_link',
 *     cookieExpires: 48,
 *     variations: {
 *         'v=1': 25,
 *         'v=2': 25,
 *         'v=3': 25
 *     }
 * });
 *
 * cop.init();
 *
 *
 * @param Object config: Object literal containing the following:
 *      String id (required): Unique-ish string for cookie identification.
 *          Only needs to be unique to other currently running tests.
 *      Number cookieExpires (optional): Number of hours browser should remember
 *          the variation chosen for the user. Defaults to 24 (hours). A value
 *          of 0 will result in a session-length cookie.
 *      Object variations (required): Object holding key/value pairs of
 *          variations and their respective traffic percentages. Example:
 *
 *          variations: {
 *              'v=1': 20,
 *              'v=2': 20,
 *              'v=3': 20
 *          }
 */
Mozilla.TrafficCop = function(config) {
    'use strict';

    // make sure config is an object
    config = (typeof config === 'object') ? config : {};

    // store id
    this.id = config.id;

    // store variations
    this.variations = config.variations;

    // store total percentage of users targeted
    this.totalPercentage = 0;

    // store experiment cookie expiry (defaults to 24 hours)
    this.cookieExpires = (config.cookieExpires !== undefined) ? config.cookieExpires : 24;

    this.redirectVariation = null;

    // calculate and store total percentage of variations
    for (var v in this.variations) {
        if (this.variations.hasOwnProperty(v) && typeof this.variations[v] === 'number') {
            this.totalPercentage += this.variations[v];
        }
    }

    return this;
};

Mozilla.TrafficCop.noVariationCookieValue = 'novariation';

/*
 * Initialize the traffic cop. Validates variations, ensures user is not
 * currently viewing a variation, and (possibly) redirects to a variation
 */
Mozilla.TrafficCop.prototype.init = function() {
    var redirectUrl;

    // respect the DNT
    if (typeof Mozilla.dntEnabled === 'function' && Mozilla.dntEnabled()) {
        return;
    }

    // If cookie helper is not defined or cookies are not enabled, do nothing.
    if (typeof Mozilla.Cookies === 'undefined' || !Mozilla.Cookies.enabled()) {
        return;
    }

    // make sure config is valid (id & variations present)
    if (this.verifyConfig()) {
        // make sure current page doesn't match a variation
        // (to avoid infinite redirects)
        if (!this.isVariation()) {
            // roll the dice to see if user should be send to a variation
            redirectUrl = this.generateRedirectUrl();

            if (redirectUrl) {
                // if we get a variation, send the user and store a cookie
                if (redirectUrl !== Mozilla.TrafficCop.noVariationCookieValue) {
                    Mozilla.Cookies.setItem(this.id, this.redirectVariation, this.cookieExpiresDate());
                    window.location.href = redirectUrl;
                }
            } else {
                // if no variation, set a cookie so user isn't re-entered into
                // the dice roll on next page load
                Mozilla.Cookies.setItem(this.id, Mozilla.TrafficCop.noVariationCookieValue, this.cookieExpiresDate());
            }
        }
    }
};

/*
 * Ensures variations were provided and in total capture between 1 and 99%
 * of users.
 */
Mozilla.TrafficCop.prototype.verifyConfig = function() {
    if (!this.id || typeof this.id !== 'string') {
        return false;
    }

    // make sure totalPercent is between 0 and 100
    if (this.totalPercentage === 0 || this.totalPercentage > 100) {
        return false;
    }

    // make sure cookieExpires is null or a number
    if (typeof this.cookieExpires !== 'number') {
        return false;
    }

    return true;
};

/*
 * Generates an expiration date for the visitor's cookie.
 * 'date' param used only for unit testing.
 */
Mozilla.TrafficCop.prototype.cookieExpiresDate = function(date) {
    // default to null, meaning a session-length cookie
    var d = null;

    if (this.cookieExpires > 0) {
        d = date || new Date();
        d.setHours(d.getHours() + this.cookieExpires);
    }

    return d;
};

/*
 * Checks to see if user is currently viewing a variation.
 */
Mozilla.TrafficCop.prototype.isVariation = function(queryString) {
    var isVariation = false;
    queryString = queryString || window.location.search;

    // check queryString for presence of variation
    for (var v in this.variations) {
        if (queryString.indexOf('?' + v) > -1 || queryString.indexOf('&' + v) > -1) {
            isVariation = true;
            break;
        }
    }

    return isVariation;
};

/*
 * Generates a random percentage (between 1 and 100, inclusive) and determines
 * which (if any) variation should be matched.
 */
Mozilla.TrafficCop.prototype.generateRedirectUrl = function(url) {
    var hash;
    var rando;
    var redirect;
    var runningTotal;
    var urlParts;

    // url parameter only supplied for unit tests
    url = url || window.location.href;

    // strip hash from URL (if present)
    if (url.indexOf('#') > -1) {
        urlParts = url.split('#');
        url = urlParts[0];
        hash = urlParts[1];
    }

    // check to see if user has a cookie from a previously visited variation
    // also make sure variation in cookie is still valid (you never know)
    if (Mozilla.Cookies.hasItem(this.id)) {
        // if the cookie is a variation, grab it and proceed
        if (this.variations[Mozilla.Cookies.getItem(this.id)]) {
            this.redirectVariation = Mozilla.Cookies.getItem(this.id);
        // if the cookie is no variation, return the unset redirect to keep user
        // in the same (no variation) cohort
        } else if (Mozilla.Cookies.getItem(this.id) === Mozilla.TrafficCop.noVariationCookieValue) {
            return Mozilla.TrafficCop.noVariationCookieValue;
        }
    } else {
        // conjure a random number between 1 and 100 (inclusive)
        rando = Math.floor(Math.random() * 100) + 1;

        // make sure random number falls in the distribution range
        if (rando <= this.totalPercentage) {
            runningTotal = 0;

            // loop through all variations
            for (var v in this.variations) {
                // check if random number falls within current variation range
                if (rando <= (this.variations[v] + runningTotal)) {
                    this.redirectVariation = v;
                    break;
                }

                // tally variation percentages for the next loop iteration
                runningTotal += this.variations[v];
            }
        }
    }

    // if a variation was chosen, construct a new URL
    if (this.redirectVariation) {
        redirect = url + (url.indexOf('?') > -1 ? '&' : '?') + this.redirectVariation;

        // re-insert hash (if originally present)
        if (hash) {
            redirect += '#' + hash;
        }
    }

    return redirect;
};
