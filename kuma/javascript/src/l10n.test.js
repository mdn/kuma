//@flow

import { localize, getLocale, gettext, ngettext, interpolate } from './l10n.js';

describe('getLocale', () => {
    let emptyData = { catalog: {}, plural: null };

    it('default value', () => {
        expect(getLocale()).toBe('en-US');
    });
    it('value can be set with localize()', () => {
        localize('en-pt', emptyData);
        expect(getLocale()).toBe('en-pt');
        localize('en-uk', emptyData);
        expect(getLocale()).toBe('en-uk');
        localize('', emptyData);
        expect(getLocale()).toBe('en-US');
        // $FlowFixMe$: purposely testing bad data
        localize(null, emptyData);
        expect(getLocale()).toBe('en-US');
    });
});

describe('gettext', () => {
    it('by default returns the input string', () => {
        expect(gettext('')).toBe('');
        expect(gettext('foo!')).toBe('foo!');
        expect(gettext('__bar&&##')).toBe('__bar&&##');
    });

    it('returns the input string when no data or bad data', () => {
        // $FlowFixMe$: purposely testing bad data
        localize('test', null);
        expect(gettext('')).toBe('');
        expect(gettext('foo!')).toBe('foo!');
        expect(gettext('__bar&&##')).toBe('__bar&&##');

        // $FlowFixMe$: purposely testing bad data
        localize('test', {});
        expect(gettext('')).toBe('');
        expect(gettext('foo!')).toBe('foo!');
        expect(gettext('__bar&&##')).toBe('__bar&&##');

        localize('test', { catalog: {}, plural: null });
        expect(gettext('')).toBe('');
        expect(gettext('foo!')).toBe('foo!');
        expect(gettext('__bar&&##')).toBe('__bar&&##');
    });

    it('works with a django-style string catalog', () => {
        localize('test', {
            catalog: {
                '': 'translated empty string',
                'foo!': 'bar!',
                '__bar&&##': 'gibberish',
                singular: ['one', 'many'],
                // This should not happen, but I want to test that we
                // handle it if data is bad.
                // $FlowFixMe$ (purposeful type error we're supressing)
                'null string': null
            },
            plural: null
        });
        expect(gettext('')).toBe('translated empty string');
        expect(gettext('foo!')).toBe('bar!');
        expect(gettext('__bar&&##')).toBe('gibberish');
        expect(gettext('singular')).toBe('one');
        expect(gettext('null string')).toBe('null string');
        expect(gettext('missing')).toBe('missing');
    });
});

describe('ngettext', () => {
    it('with no catalog, returns supplied singular or plural', () => {
        expect(ngettext('s', 'p', 0)).toBe('p');
        expect(ngettext('s', 'p', 1)).toBe('s');
        expect(ngettext('s', 'p', 2)).toBe('p');
        expect(ngettext('s', 'p', 20)).toBe('p');
        expect(ngettext('s', 'p', -1)).toBe('p');
        expect(ngettext('s', 'p', 6.02e23)).toBe('p');
    });

    it('Returns untranslated text when no translation available', () => {
        // $FlowFixMe$: purposely testing bad data
        localize('test', null);
        expect(ngettext('s', 'p', 1)).toBe('s');
        expect(ngettext('s', 'p', 2)).toBe('p');
        expect(ngettext('s', 'p', 3)).toBe('p');

        // $FlowFixMe$: purposely testing bad data
        localize('test', {});
        expect(ngettext('s', 'p', 1)).toBe('s');
        expect(ngettext('s', 'p', 2)).toBe('p');
        expect(ngettext('s', 'p', 3)).toBe('p');

        localize('test', {
            catalog: { t: 'translation' },
            plural: '(n >=1 && n <= 4) ? n-1 : 4'
        });
        expect(ngettext('s', 'p', 1)).toBe('s');
        expect(ngettext('s', 'p', 2)).toBe('p');
        expect(ngettext('s', 'p', 3)).toBe('p');
    });

    it('Uses english pluralization rules by default', () => {
        localize('test', {
            catalog: { s: ['singular', 'plural'] },
            plural: null
        });
        expect(ngettext('s', 'p', 0)).toBe('plural');
        expect(ngettext('s', 'p', 1)).toBe('singular');
        expect(ngettext('s', 'p', 2)).toBe('plural');
        expect(ngettext('s', 'p', 20)).toBe('plural');
        expect(ngettext('s', 'p', -1)).toBe('plural');
        expect(ngettext('s', 'p', 6.02e23)).toBe('plural');
    });

    it('Supports custom pluralization rules', () => {
        localize('test', {
            catalog: { s: ['one', 'two', 'three', 'four', 'many'] },
            plural: '(n >=1 && n <= 4) ? n-1 : 4'
        });
        expect(ngettext('s', 'p', 1)).toBe('one');
        expect(ngettext('s', 'p', 2)).toBe('two');
        expect(ngettext('s', 'p', 3)).toBe('three');
        expect(ngettext('s', 'p', 4)).toBe('four');
        expect(ngettext('s', 'p', 0)).toBe('many');
        expect(ngettext('s', 'p', -1)).toBe('many');
        expect(ngettext('s', 'p', 20)).toBe('many');
    });

    it('Returns singular if no plural forms available', () => {
        localize('test', {
            catalog: { s: 't' },
            plural: '(n >=1 && n <= 4) ? n-1 : 4'
        });
        expect(ngettext('s', 'p', 1)).toBe('t');
        expect(ngettext('s', 'p', 2)).toBe('t');
        expect(ngettext('s', 'p', 3)).toBe('t');
    });
});

describe('interpolate()', () => {
    it('two argument form', () => {
        expect(interpolate('foo', [])).toBe('foo');
        expect(interpolate('%s', [1])).toBe('1');
        expect(interpolate('%s%s%s', [1, 2, 3])).toBe('123');
        expect(interpolate('%s%s', [1, 2, 3])).toBe('12');
        expect(interpolate('%s%s%s%s', [1, 2, 3])).toBe('123undefined');
        expect(interpolate('%s foo %s', [1, true])).toBe('1 foo true');
        expect(interpolate('A%sfoo%sZ', ['a', 'z'])).toBe('AafoozZ');
    });

    it('three argument form, with an array', () => {
        expect(interpolate('foo', [], true)).toBe('foo');
        expect(interpolate('%(0)s', [1], true)).toBe('1');
        expect(interpolate('%(1)s foo %(0)s', [1, true], true)).toBe(
            'true foo 1'
        );
        expect(interpolate('A%(1)sfoo%(0)sZ', ['a', 'z'], true)).toBe(
            'AzfooaZ'
        );
        expect(interpolate('%(0)s%(1)s%(2)s', [1, 2, 3], true)).toBe('123');
        expect(interpolate('%(2)s%(2)s', [1, 2, 3], true)).toBe('33');
        expect(interpolate('%(0)s%(1)s%(5)s', [1, 2, 3], true)).toBe(
            '12undefined'
        );
    });

    it('three argument form, with object', () => {
        expect(interpolate('foo', {}, true)).toBe('foo');
        expect(interpolate('%(a)s', { a: 1 }, true)).toBe('1');
        expect(interpolate('%(b)s foo %(a)s', { a: 1, b: true }, true)).toBe(
            'true foo 1'
        );
        expect(interpolate('A%(z)sfoo%(a)sZ', { a: 'a', z: 'z' }, true)).toBe(
            'AzfooaZ'
        );
        expect(interpolate('%(a)s%(b)s%(d)s', { a: 1, b: 2, c: 3 }, true)).toBe(
            '12undefined'
        );
    });
});
