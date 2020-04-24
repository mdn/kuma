import { formatDate } from './formatDate.js';

describe('formatDate()', () => {
    // in order for tests to pass in Docker, we have to stick
    // with the default locale that Node 12 provides, which is `en-US`.
    const locale = 'en-US';
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
    it('returns empty string for invalid date', () => {
        const mockDate = '11/9999';
        expect(formatDate(locale, mockDate)).toEqual('');
    });
});
