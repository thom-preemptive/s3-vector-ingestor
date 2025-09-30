import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import App from './App';

// Determine environment from various sources
const getEnvironment = () => {
  // Check Amplify environment variable first
  const amplifyEnv = process.env.REACT_APP_AMPLIFY_ENV || process.env.AWS_BRANCH;
  
  // Check custom environment variable
  const customEnv = process.env.REACT_APP_ENVIRONMENT;
  
  // Check hostname for deployed environments
  const hostname = window.location.hostname;
  if (hostname.includes('main.') || hostname.includes('prod')) return 'main';
  if (hostname.includes('test.')) return 'test';
  if (hostname.includes('dev.')) return 'dev';
  
  // Fallback order: amplifyEnv -> customEnv -> 'dev'
  return amplifyEnv || customEnv || 'dev';
};

const environment = getEnvironment();

// Configure Cognito based on environment
const getCognitoConfig = (env: string) => {
  const region = process.env.REACT_APP_AWS_REGION || 'us-east-1';
  
  // Environment-specific user pool IDs (these will be set via Amplify environment variables)
  const userPoolIds = {
    dev: process.env.REACT_APP_COGNITO_USER_POOL_ID_DEV || 'us-east-1_PLACEHOLDER_DEV',
    test: process.env.REACT_APP_COGNITO_USER_POOL_ID_TEST || 'us-east-1_PLACEHOLDER_TEST',
    main: process.env.REACT_APP_COGNITO_USER_POOL_ID_MAIN || 'us-east-1_PLACEHOLDER_MAIN'
  };
  
  // Environment-specific client IDs
  const clientIds = {
    dev: process.env.REACT_APP_COGNITO_CLIENT_ID_DEV || 'PLACEHOLDER_CLIENT_ID_DEV',
    test: process.env.REACT_APP_COGNITO_CLIENT_ID_TEST || 'PLACEHOLDER_CLIENT_ID_TEST',
    main: process.env.REACT_APP_COGNITO_CLIENT_ID_MAIN || 'PLACEHOLDER_CLIENT_ID_MAIN'
  };
  
  return {
    region,
    userPoolId: userPoolIds[env as keyof typeof userPoolIds] || userPoolIds.dev,
    userPoolClientId: clientIds[env as keyof typeof clientIds] || clientIds.dev
  };
};

const cognitoConfig = getCognitoConfig(environment);

// Configure Amplify with environment-specific settings
const amplifyConfig = {
  Auth: {
    Cognito: {
      region: cognitoConfig.region,
      userPoolId: cognitoConfig.userPoolId,
      userPoolClientId: cognitoConfig.userPoolClientId,
    }
  },
  API: {
    REST: {
      'api': {
        endpoint: process.env.REACT_APP_API_URL || 'https://api.example.com',
        region: cognitoConfig.region
      }
    }
  }
};

console.log(`agent2_ingestor: Environment detected as '${environment}'`);
console.log(`agent2_ingestor: Using Cognito User Pool: ${cognitoConfig.userPoolId}`);

Amplify.configure(amplifyConfig);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);