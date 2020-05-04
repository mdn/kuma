import { formatDate, formatMoney } from './formatters.js';

// Node v12 doesn't support Intl out-of-the-box, so in order for tests to
// pass in Docker, we have to write tests using the default locale, `en-US`.
const locale = 'en-US';

describe('formatDate()', () => {
    it('if no options are provided, formats date in long month and numeric date and year', () => {
        const mockDate = '2020-05-23T08:04:40';
        const expected = 'May 23, 2020';
        expect(formatDate(locale, mockDate)).toEqual(expected);
    });
    it('formats date according to options', () => {
        const mockDate = '2020-05-23T08:04:40';
        const mockOptions = {
            year: '2-digit',
            month: '2-digit',
        };
        const expected = '05/20';
        expect(formatDate(locale, mockDate, mockOptions)).toEqual(expected);
    });
    it('throws error for invalid date', () => {
        const mockDate = '11/9999';
        expect(() => formatDate(locale, mockDate)).toThrowError('Invalid date');
    });
});

describe('formatMoney()', () => {
    it('if no options are provided, formats money to USD whole-dollars', () => {
        const mockAmount = 10;
        const expected = '$10';
        expect(formatMoney(locale, mockAmount)).toEqual(expected);
    });
    it('accepts amounts that are strings', () => {
        const mockAmount = '1099';
        const expected = '$1,099';
        expect(formatMoney(locale, mockAmount)).toEqual(expected);
    });
    it('formats with respect to other options', () => {
        const mockAmount = '1099';
        const expected = '1,099.00';
        const mockOptions = {
            minimumFractionDigits: 2,
            currencyDisplay: 'name',
        };
        expect(formatMoney(locale, mockAmount, mockOptions)).toEqual(expected);
    });
});
