//@flow
import React from 'react';
import renderer from 'react-test-renderer';
import {
    localize,
    getLocale,
    gettext,
    ngettext,
    interpolate,
    Interpolated
} from './l10n';

// We don't actually want the strings in this file to be extracted
// for localization, so we're going to use non-standard aliases
// for gettext and ngettext.
const gtext = gettext;
const ngtext = ngettext;

describe('getLocale', () => {
    it('default value', () => {
        expect(getLocale()).toBe('en-US');
    });
    it('value can be set with localize()', () => {
        localize('en-pt', {}, null);
        expect(getLocale()).toBe('en-pt');
        localize('en-uk', {}, null);
        expect(getLocale()).toBe('en-uk');
        localize('', {});
        expect(getLocale()).toBe('en-US');
        // $FlowFixMe$: purposely testing bad data
        localize(null, {});
        expect(getLocale()).toBe('en-US');
    });
});

describe('gettext', () => {
    it('by default returns the input string', () => {
        expect(gtext('')).toBe('');
        expect(gtext('foo!')).toBe('foo!');
        expect(gtext('__bar&&##')).toBe('__bar&&##');
    });

    it('returns the input string when no data or bad data', () => {
        // $FlowFixMe$: purposely testing bad data
        localize('test', null);
        expect(gtext('')).toBe('');
        expect(gtext('foo!')).toBe('foo!');
        expect(gtext('__bar&&##')).toBe('__bar&&##');

        localize('test', {});
        expect(gtext('')).toBe('');
        expect(gtext('foo!')).toBe('foo!');
        expect(gtext('__bar&&##')).toBe('__bar&&##');
    });

    it('works with a django-style string catalog', () => {
        localize('test', {
            '': 'translated empty string',
            'foo!': 'bar!',
            '__bar&&##': 'gibberish',
            singular: ['one', 'many'],
            // This should not happen, but I want to test that we
            // handle it if data is bad.
            // $FlowFixMe$ (purposeful type error we're supressing)
            'null string': null
        });

        expect(gtext('')).toBe('translated empty string');
        expect(gtext('foo!')).toBe('bar!');
        expect(gtext('__bar&&##')).toBe('gibberish');
        expect(gtext('singular')).toBe('one');
        expect(gtext('null string')).toBe('null string');
        expect(gtext('missing')).toBe('missing');
    });
});

describe('ngettext', () => {
    it('with no catalog, returns supplied singular or plural', () => {
        expect(ngtext('s', 'p', 0)).toBe('p');
        expect(ngtext('s', 'p', 1)).toBe('s');
        expect(ngtext('s', 'p', 2)).toBe('p');
        expect(ngtext('s', 'p', 20)).toBe('p');
        expect(ngtext('s', 'p', -1)).toBe('p');
        expect(ngtext('s', 'p', 6.02e23)).toBe('p');
    });

    it('Returns untranslated text when no translation available', () => {
        // $FlowFixMe$: purposely testing bad data
        localize('test', null);
        expect(ngtext('s', 'p', 1)).toBe('s');
        expect(ngtext('s', 'p', 2)).toBe('p');
        expect(ngtext('s', 'p', 3)).toBe('p');

        localize('test', {});
        expect(ngtext('s', 'p', 1)).toBe('s');
        expect(ngtext('s', 'p', 2)).toBe('p');
        expect(ngtext('s', 'p', 3)).toBe('p');

        localize('test', { t: 'translation' }, n =>
            n >= 1 && n <= 4 ? n - 1 : 4
        );
        expect(ngtext('s', 'p', 1)).toBe('s');
        expect(ngtext('s', 'p', 2)).toBe('p');
        expect(ngtext('s', 'p', 3)).toBe('p');
    });

    it('Uses english pluralization rules by default', () => {
        localize('test', { s: ['singular', 'plural'] }, null);
        expect(ngtext('s', 'p', 0)).toBe('plural');
        expect(ngtext('s', 'p', 1)).toBe('singular');
        expect(ngtext('s', 'p', 2)).toBe('plural');
        expect(ngtext('s', 'p', 20)).toBe('plural');
        expect(ngtext('s', 'p', -1)).toBe('plural');
        expect(ngtext('s', 'p', 6.02e23)).toBe('plural');
    });

    it('Supports custom pluralization rules', () => {
        localize('test', { s: ['one', 'two', 'three', 'four', 'many'] }, n =>
            n >= 1 && n <= 4 ? n - 1 : 4
        );
        expect(ngtext('s', 'p', 1)).toBe('one');
        expect(ngtext('s', 'p', 2)).toBe('two');
        expect(ngtext('s', 'p', 3)).toBe('three');
        expect(ngtext('s', 'p', 4)).toBe('four');
        expect(ngtext('s', 'p', 0)).toBe('many');
        expect(ngtext('s', 'p', -1)).toBe('many');
        expect(ngtext('s', 'p', 20)).toBe('many');
    });

    it('Returns singular if no plural forms available', () => {
        localize('test', { s: 't' }, n => (n >= 1 && n <= 4 ? n - 1 : 4));
        expect(ngtext('s', 'p', 1)).toBe('t');
        expect(ngtext('s', 'p', 2)).toBe('t');
        expect(ngtext('s', 'p', 3)).toBe('t');
    });

    it('Returns sole plural form regardless of count', () => {
        localize('test', { s: ['t'] }, n => (n === 1 ? 0 : 1));
        expect(ngtext('s', 'p', 0)).toBe('t');
        expect(ngtext('s', 'p', 1)).toBe('t');
        expect(ngtext('s', 'p', 2)).toBe('t');
    });

    it('Returns untranslated text if plural function returns bad index', () => {
        localize('test', { s: ['t1', 't2'] }, n => n);
        expect(ngtext('s', 'p', 0)).toBe('t1');
        expect(ngtext('s', 'p', 1)).toBe('t2');
        expect(ngtext('s', 'p', 2)).toBe('p');
    });
});

describe('interpolate()', () => {
    it('takes an array', () => {
        expect(interpolate('foo', [])).toBe('foo');
        expect(interpolate('%s', [1])).toBe('1');
        expect(interpolate('%s%s%s', [1, 2, 3])).toBe('123');
        expect(interpolate('%s%s', [1, 2, 3])).toBe('12');
        expect(interpolate('%s%s%s%s', [1, 2, 3])).toBe('123undefined');
        expect(interpolate('%s foo %s', [1, true])).toBe('1 foo true');
        expect(interpolate('A%sfoo%sZ', ['a', 'z'])).toBe('AafoozZ');
    });

    it('takes an object with string parameters', () => {
        expect(interpolate('foo', {})).toBe('foo');
        expect(interpolate('%(a)s', { a: 1 })).toBe('1');
        expect(interpolate('%(b)s foo %(a)s', { a: 1, b: true })).toBe(
            'true foo 1'
        );
        expect(interpolate('A%(z)sfoo%(a)sZ', { a: 'a', z: 'z' })).toBe(
            'AzfooaZ'
        );
        expect(interpolate('%(a)s%(b)s%(d)s', { a: 1, b: 2, c: 3 })).toBe(
            '12undefined'
        );
    });
});

describe('<Interpolated/>', () => {
    it('takes element parameters', () => {
        const tree1 = renderer
            .create(
                <Interpolated
                    id="oh a <link/> wow"
                    link={<a href="/">click</a>}
                />
            )
            .toJSON();
        expect(tree1).toMatchSnapshot();

        const tree2 = renderer
            .create(
                <Interpolated
                    id="wow <head/> such <body /> many <foot />"
                    head={<h1>Beautiful</h1>}
                    foot={<p className="something">more</p>}
                />
            )
            .toJSON();
        expect(tree2).toMatchSnapshot();
    });
});
