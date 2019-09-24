/**
 * This module exports functions getLocale(), gettext(), ngettext() and
 * interpolate() that are used for localizing strings. It is configured
 * by default for English, but call the exported function localize() to
 * set it up for another locale.
 *
 * gettext() and ngettext() work based on a string catalog provided to
 * us by the Django backend. The implementation of these functions
 * (as well as the interpolate() utility) are based on the code in
 * https://github.com/django/django/blob/master/django/views/i18n.py
 * In order to work correctly, they require data in the form provided
 * by the JSONCatalog class in that file.
 *
 * @flow
 */

// This is the type of the string catalog that Django creates for a locale.
type StringCatalog = { [string]: string | Array<string> };

// The "plural index" function takes a count as its input and returns
// a number that is an index into an array of plural forms. This default
// function is suitable for English, but some languages have more than
// one plural form and require more complicated rules.
type PluralFunction = number => number;

/*
 * These are default values for the state variables that define the
 * current localization.
 */
const defaultLocale = 'en-US';
const defaultStringCatalog: StringCatalog = {};
const defaultPluralFunction: PluralFunction = n => (+n === 1 ? 0 : 1);

/*
 * The currentLocale, currentStringCatalog, and currentPluralFunction
 * variables hold the current state for this module. Their initial
 * values are the defaults above, which are suitable for untranslated
 * English text.  The localize() function defines new values for each
 * of them.
 */
let currentLocale = defaultLocale;
let currentStringCatalog: StringCatalog = defaultStringCatalog;
let currentPluralFunction: PluralFunction = defaultPluralFunction;

/**
 * This function sets up localization for the specified locale.
 * The catalog argument should be a string catalog in the form returned by
 * the JSONCatalog class in
 * https://github.com/django/django/blob/master/django/views/i18n.py
 */
export function localize(
    locale: ?string,
    catalog: ?StringCatalog,
    pluralFunction: ?PluralFunction
): void {
    currentLocale = locale || defaultLocale;
    currentStringCatalog = catalog || defaultStringCatalog;
    currentPluralFunction = pluralFunction || defaultPluralFunction;
}

// Return the locale string most recently passed to localize().
export function getLocale() {
    return currentLocale;
}

/**
 * Look up the specified English string in the string catalog for
 * the current locale and return the translation found there. If no
 * catalog exists or not translation is found, we just return the
 * untranslated English string instead.
 */
export function gettext(english: string): string {
    let translation = currentStringCatalog[english];
    if (Array.isArray(translation)) {
        // If there are multiple forms, return the first
        return translation[0];
    } else if (typeof translation === 'string') {
        // If we got a string return it
        return translation;
    } else {
        // If we didn't find a translation, just return the english.
        return english;
    }
}

/**
 * Look up translations of the specified singular English string and
 * return a form of the translation suitable for use with the specified
 * number of items. If no string catalog exists, or no translation is
 * found, then we return one of the English strings singular or plural
 * based on the value of count.
 */
export function ngettext(
    singular: string,
    plural: string,
    count: number | string
) {
    count = +count; // If we were passed a string, convert to number
    let translation = currentStringCatalog[singular];

    if (Array.isArray(translation)) {
        // If we got an array of translations, figure out which one
        // to use for this specific count
        return translation[currentPluralFunction(count)];
    } else if (typeof translation === 'string') {
        // If we only got one string, just return it, regardless
        // of the count
        return translation;
    } else {
        // If there is no data, or no translation found, then return
        // the english singular or plural.
        return count === 1 ? singular : plural;
    }
}

/**
 * This is a convenience function (often useful in conjunction with
 * ngettext()) that interpolates values from an array or properties from
 * an object into a template string and then returns the resulting string.
 *
 * If the second argument is an array, the values from that array will be
 * interpolated into the string s replacing each occurrance of the string `%s`.
 *
 * If the second argument is object then s should contain substrings of
 * the form `%(name)s`. Each substring of this form will be replaced with the
 * value of the named property of args.
 */
export function interpolate(s: string, args: Array<any> | { [string]: any }) {
    if (Array.isArray(args)) {
        return s.replace(/%s/g, () => String(args.shift()));
    } else {
        const typedArgs = args;
        return s.replace(/%\(\w+\)s/g, match =>
            String(typedArgs[match.slice(2, -2)])
        );
    }
}
