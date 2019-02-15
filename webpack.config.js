const path = require('path');
const nodePath = process.env.NODE_PATH || './node_modules';

module.exports = {
    mode: 'production',
    entry: path.resolve(__dirname, './kuma/javascript/src/index.jsx'),
    output: {
        filename: 'react.js',
        path: path.resolve(__dirname, './kuma/javascript/dist/')
    },
    module: {
        rules: [{
            test: /\.(js|jsx)$/,
            exclude: /node_modules/,
            use: {
                loader: 'babel-loader',
                options: {
                    presets: [
                        `${nodePath}/@babel/preset-env`,
                        `${nodePath}/@babel/preset-react`,
                        `${nodePath}/@babel/preset-flow`,
                    ]
                },
            }
        }]
    },
    resolve: {
        extensions: ['*', '.js', '.jsx'],
        modules: [nodePath]
    },
    resolveLoader: {
        modules: [nodePath]
    }
};
