// @flow

/**
 * Basic date formatting according to locale.
 * Defaults to long month, numeric day and year
 * e.g. for en-US, April 22, 2020
 *
 * @param {string} locale - locale identifier
 * @param {Object | string | number} date - date to be formatted
 * @param {Object} [options] - formatting options
 * @returns {string} - formatted date string
 */

type DateTimeFormatOptions = {
    localeMatcher?: 'lookup' | 'best fit',
    timeZone?: string,
    hour12?: boolean,
    formatMatcher?: 'basic' | 'best fit',
    weekday?: 'narrow' | 'short' | 'long',
    era?: 'narrow' | 'short' | 'long',
    year?: 'numeric' | '2-digit',
    month?: 'numeric' | '2-digit' | 'narrow' | 'short' | 'long',
    day?: 'numeric' | '2-digit',
    hour?: 'numeric' | '2-digit',
    minute?: 'numeric' | '2-digit',
    second?: 'numeric' | '2-digit',
    timeZoneName?: 'short' | 'long',
};

export const formatDate = (
    locale: string,
    date: Date | number | string,
    options?: DateTimeFormatOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    }
): string => {
    const dateObj = new Date(date);
    if (dateObj instanceof Date && isNaN(dateObj.valueOf())) {
        throw new Error('Invalid date');
    }
    return new Intl.DateTimeFormat(locale, options).format(dateObj);
};
