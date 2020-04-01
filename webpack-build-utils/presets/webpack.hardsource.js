const HardSourceWebpackPlugin = require('hard-source-webpack-plugin');

// for more on this plugin see https://github.com/mzgoddard/hard-source-webpack-plugin
module.exports = () => ({
    plugins: [new HardSourceWebpackPlugin()],
});
