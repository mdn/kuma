var mdn = window.mdn || {};
var paymentsHandlerUtils = {
    /**
     * If the `selectedAmount` isNaN or less than 1, return and empty
     * string else, prepend a dollar symbol and return.
     * NOTE: This function relies on JavaScript's loose string-to-number conversions
     * @param {String|Number} selectedAmount - The number to process
     * @returns `selectedAmount` prefixed with a dollar symbol, or an empty string
     */
    addCurrencyPrefix: function(selectedAmount) {
        'use strict';
        return isNaN(selectedAmount) || selectedAmount < 1
            ? ''
            : '$' + selectedAmount;
    },
    getSelectedAmount: function(value) {
        'use strict';
        return value % 1 === 0 ? parseInt(value, 10) : parseFloat(value).toFixed(2);
    }
};

/* First step towards using actual modules for our JS.
   This will allow unit testing, and */
if (typeof exports === 'object') {
    module.exports = paymentsHandlerUtils;
}

/* this will ensure it also works in the browser,
   without yet needing Babel */
mdn.paymentsHandlerUtils = paymentsHandlerUtils;
