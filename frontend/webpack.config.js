const { ModuleFederationPlugin } = require("webpack").container;
const path = require("path");

module.exports = {
  entry: "./src/index",
  output: {
    path: path.resolve(__dirname, "../dist/frontend/dist"),
    publicPath: "auto",
    clean: true,
  },
  resolve: {
    extensions: [".tsx", ".ts", ".jsx", ".js"],
  },
  module: {
    rules: [
      {
        test: /\.(tsx?|jsx?)$/,
        use: "babel-loader",
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  plugins: [
    new ModuleFederationPlugin({
      name: "nlExplorer",
      filename: "remoteEntry.js",
      exposes: {
        "./index": "./src/index",
      },
      shared: {
        react: { singleton: true, requiredVersion: "^18.0.0" },
        "react-dom": { singleton: true, requiredVersion: "^18.0.0" },
        "@apache-superset/core": { singleton: true, import: false },
      },
    }),
  ],
};
