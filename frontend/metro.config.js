const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Workaround for Metro/Expo SDK 53 compatibility
config.resolver = {
  ...config.resolver,
  unstable_enablePackageExports: true,
  resolverMainFields: ['react-native', 'browser', 'main'],
};

module.exports = config;