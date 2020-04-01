const path = require('path');

const clientConfig = {
    entry: path.resolve(__dirname, '../../kuma/javascript/src/index.jsx'),
    output: {
        path: path.resolve(__dirname, '../../kuma/javascript/dist/'),
    },
};

module.exports = () => clientConfig;
