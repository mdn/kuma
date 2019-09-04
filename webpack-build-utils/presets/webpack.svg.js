module.exports = () => ({
    module: {
        rules: [
            {
                test: /\.svg$/,
                exclude: /node_modules/,
                use: [
                    {
                        loader: 'babel-loader'
                    },
                    {
                        loader: 'react-svg-loader',
                        options: {
                            jsx: true, // true outputs JSX tags
                            svgo: {
                                // Disable this one svgo plugin because it
                                // strips the role attribute from our svgs
                                plugins: [{ removeUnknownsAndDefaults: false }]
                            }
                        }
                    }
                ]
            }
        ]
    }
});
