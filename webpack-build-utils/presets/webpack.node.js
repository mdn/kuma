const path = require('path');

module.exports = () => ({
    target: 'node',
    entry: path.resolve(__dirname, '../../kuma/javascript/src/ssr.jsx'),
    output: {
        filename: 'ssr.js',
        path: path.resolve(__dirname, '../../kuma/javascript/dist/'),
        libraryExport: 'default',
        libraryTarget: 'commonjs2'
    }
});
