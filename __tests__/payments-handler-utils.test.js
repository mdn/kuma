const paymentsHandlerUtils = require('../kuma/static/js/components/payments/payments-handler-utils.js');

describe('addCurrencyPrefix', function() {
    it('returns an empty string for non numerals and values less that 1', function() {
        expect(paymentsHandlerUtils.addCurrencyPrefix(0.5)).toEqual('');
        expect(paymentsHandlerUtils.addCurrencyPrefix('ten')).toEqual('');
    });

    it('returns a dollar amount as a string for values greater than 1', function() {
        expect(paymentsHandlerUtils.addCurrencyPrefix(1)).toEqual('$1');
        expect(paymentsHandlerUtils.addCurrencyPrefix('10')).toEqual('$10');
    });
});

describe('getSelectedAmount', function() {
    it('returns an integer for whole numbers', function() {
        expect(paymentsHandlerUtils.getSelectedAmount(1)).toEqual(1);
        expect(paymentsHandlerUtils.getSelectedAmount('2')).toEqual(2);
        expect(typeof 10).toEqual(typeof paymentsHandlerUtils.getSelectedAmount('10'));
    });

    it('returns a floating point number as a string, limited to two decimal places for decimal values', function() {
        expect(paymentsHandlerUtils.getSelectedAmount(1.2345)).toEqual('1.23');
        expect(paymentsHandlerUtils.getSelectedAmount(1.2)).toEqual('1.20');
        expect(paymentsHandlerUtils.getSelectedAmount('10.9')).toEqual('10.90');
    });
});
