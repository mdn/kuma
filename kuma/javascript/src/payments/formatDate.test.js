import { formatDate } from './formatDate.js';

describe('formatDate()', () => {
    it('if no options are provided, formats date in long month and numeric date and year', () => {
        const mockDate = '2020-05-23T08:04:40';
        const expected = 'May 23, 2020';
        expect(formatDate('en-US', mockDate)).toEqual(expected);
    });
    it('formats date according to locale', () => {
        const mockDate = 1590149080000;
        const expected = '22 de maio de 2020';
        expect(formatDate('pt-PT', mockDate)).toEqual(expected);
    });
    it('formats date according to options', () => {
        const mockDate = '2020-05-23T08:04:40';
        const mockOptions = {
            year: '2-digit',
            month: '2-digit',
        };
        const expected = '05.20';
        expect(formatDate('tr', mockDate, mockOptions)).toEqual(expected);
    });
    it('returns empty string for invalid date', () => {
        const mockDate = '11/9999';
        expect(formatDate('en-US', mockDate)).toEqual('');
    });
});
