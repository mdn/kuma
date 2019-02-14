const path = require('path');

module.exports = {
    mode: "production",
    entry: path.resolve(__dirname, './kuma/javascript/src/index.jsx'),
    output: {
        filename: 'react.js',
        path: path.resolve(__dirname, './kuma/javascript/dist/')
    },
    module: {
        rules: [{
            "test": /\.(js|jsx)$/,
            "exclude": /node_modules/,
            "use": {
                "loader": "babel-loader",
                "options": {
                    "presets": [
                        "@babel/preset-env",
                        "@babel/preset-react",
                        "@babel/preset-flow",
                    ]
                }
            }
        }]
    }
};
