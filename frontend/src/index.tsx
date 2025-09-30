import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import App from './App';

// Get Cognito configuration from environment variables
const cognitoConfig = {
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || 'us-east-1_ZXccV9Ntq',
  userPoolClientId: process.env.REACT_APP_COGNITO_CLIENT_ID || '3u5hedl2mp0bvg5699l16dj4oe'
};

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

console.log(`agent2_ingestor: Using Cognito User Pool: ${cognitoConfig.userPoolId}`);
console.log(`agent2_ingestor: Using Client ID: ${cognitoConfig.userPoolClientId}`);

Amplify.configure(amplifyConfig);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);