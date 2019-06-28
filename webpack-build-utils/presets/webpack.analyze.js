const BundleAnalyzerPlugin = require('webpack-bundle-analyzer')
    .BundleAnalyzerPlugin;

// for more on this plugin see https://github.com/webpack-contrib/webpack-bundle-analyzer
module.exports = () => ({
    plugins: [
        new BundleAnalyzerPlugin({
            defaultSizes: 'gzip'
        })
    ]
});
