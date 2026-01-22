const path = require('path');

module.exports = {
  mode: 'production',
  entry: './src/jupyter-lite-route.ts',
  output: {
    path: path.resolve(__dirname),
    filename: 'jupyter-lite-route.js',
    library: {
      type: 'module',
    },
  },
  experiments: {
    outputModule: true,
  },
  resolve: {
    extensions: ['.ts', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.ts$/,
        use: {
          loader: 'ts-loader',
          options: {
            configFile: 'tsconfig.route.json',
          },
        },
        exclude: /node_modules/,
      },
    ],
  },
};
