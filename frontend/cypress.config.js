const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    env: {
      apiUrl: 'http://localhost:8000/api',
    },
    setupNodeEvents(on, config) {
      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
      });
    },
    // Retry settings for flaky tests
    retries: {
      runMode: 2,
      openMode: 0,
    },
    // Default command timeout
    defaultCommandTimeout: 30000,
    // Request timeout
    requestTimeout: 30000,
    // Response timeout
    responseTimeout: 30000,
    // Page load timeout
    pageLoadTimeout: 60000,
    // Debug settings
    watchForFileChanges: true,
    // Log settings
    logLevel: 'debug',
    // Screenshot settings
    screenshotOnRunFailure: true,
    trashAssetsBeforeRuns: true,
    // Video settings
    video: true,
    videoCompression: 32,
    // Browser settings
    chromeWebSecurity: false,
    // Additional settings for debugging
    experimentalStudio: true,
    experimentalRunAllSpecs: true,
    experimentalMemoryManagement: true,
  },
  
  component: {
    devServer: {
      framework: 'create-react-app',
      bundler: 'webpack',
    },
    specPattern: 'cypress/component/**/*.cy.{js,jsx,ts,tsx}',
  },
}); 