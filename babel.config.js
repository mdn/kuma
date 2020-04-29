const path = require('path');

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
const nodePath = process.env.NODE_PATH || path.join(__dirname, 'node_modules');

module.exports = (api) => {
    api.cache(() => process.env.NODE_ENV);
    const presets = [
        path.join(nodePath, '@babel/preset-react'),
        path.join(nodePath, '@babel/preset-flow'),
        [
            path.join(nodePath, '@babel/preset-env'),
            {
                targets: {
                    browsers: 'last 2 versions',
                },
            },
        ],
    ];
    const plugins = [
        path.join(nodePath, '@babel/plugin-proposal-class-properties'),
        path.join(nodePath, '@babel/plugin-transform-runtime'),
    ];

    return {
        presets,
        plugins,
    };
};
