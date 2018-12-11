var mdn = window.mdn || {};
var paymentsHandlerUtils = {
    getNewValue: function(selectedAmount) {
        'use strict';
        return selectedAmount < 1 || isNaN(selectedAmount)
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

/* this will ensure it also work in the browser,
   without yet needing Babel */
mdn.paymentsHandlerUtils = paymentsHandlerUtils;
