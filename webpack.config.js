const path = require('path');

const webpack = require('webpack');
const webpackMerge = require('webpack-merge');

// When running in docker, we install libraries into /tools/node_modules
// so that we don't overwrite the user's local kuma/node_modules directory
// with linux versions of modules (like the binary newrelic module).
// To make this work, the docker container sets the NODE_PATH environment
// variable so that code can be found in /tools/node_modules.
// But we also have to convince webpack and babel to use the /tools
// directory when we're running in docker, so this nodePath constant
// is the absolute path to the node_modules directory we want to use.
// We set it on resolve.modules below, and prepend it to the name of
// all the babel plugins so we're sure we're gettting precisely the
// file we want both locally (NODE_PATH not set) and in docker.
//
// TODO: there ought to be a better way to do this.
//
const nodePath = (process.env.NODE_PATH && process.env.NODE_PATH.split(path.delimiter)) || [path.join(__dirname, 'node_modules')];
const modeConfig = env => require(`./webpack-build-utils/webpack.${env}`)(env);
const presetsConfig = require('./webpack-build-utils/loadPresets');

module.exports = ({ mode, presets } = { mode: 'production', presets: [] }) => {
    const merged = webpackMerge(
        {
            mode,
            module: {
                rules: [
                    {
                        test: /\.jsx?$/,
                        exclude: /node_modules/,
                        use: {
                            loader: 'babel-loader'
                        }
                    }
                ]
            },
            resolve: {
                modules: nodePath
            },
            resolveLoader: {
                modules: nodePath
            },
            output: {
                filename: 'react.js'
            },
            plugins: [new webpack.ProgressPlugin()]
        },
        modeConfig(mode),
        presetsConfig({ mode, presets })
    );

    return merged;
};
