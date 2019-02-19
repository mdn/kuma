const path = require('path');
const nodePath = process.env.NODE_PATH || './node_modules';

module.exports = {
//    mode: "development",
    mode: "production",
    entry: path.resolve(__dirname, './kuma/javascript/src/index.jsx'),
    output: {
        filename: 'react.js',
        path: path.resolve(__dirname, './kuma/javascript/dist/')
    },
    module: {
        rules: [{
            "test": /\.jsx?$/,
            "exclude": /node_modules/,
            "use": {
                "loader": "babel-loader",
                "options": {
                    "presets": [
                        "@babel/preset-env",
                        "@babel/preset-react",
                        "@babel/preset-flow",
                        "@emotion/babel-preset-css-prop"
                    ],
                    "plugins": [
                        "@babel/plugin-proposal-class-properties"
                    ]
                }
            }
        }]
    },
    resolve: {
        modules: [nodePath]
    },
    resolveLoader: {
        modules: [nodePath]
    }
};
