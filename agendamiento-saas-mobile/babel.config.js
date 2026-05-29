module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      ['babel-preset-expo', { jsxImportSource: 'nativewind' }],
      'nativewind/babel',
    ],
    // Reanimated 4 requiere react-native-worklets/plugin (siempre LAST)
    plugins: ['react-native-worklets/plugin'],
  };
};
