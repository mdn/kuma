const path = require('path');

module.exports = () => ({
    target: 'web',
    entry: path.resolve(__dirname, '../../kuma/javascript/src/bcd-signal.jsx'),
    output: {
        filename: 'bcd-signal.js',
        path: path.resolve(__dirname, '../../kuma/javascript/dist/')
    }
});
