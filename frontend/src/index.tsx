import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import App from './App';

// Configure Amplify (you'll need to add your actual config)
const amplifyConfig = {
  Auth: {
    Cognito: {
      region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
      userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || '',
      userPoolClientId: process.env.REACT_APP_COGNITO_CLIENT_ID || '',
    }
  },
  API: {
    REST: {
      'api': {
        endpoint: process.env.REACT_APP_API_URL || 'http://localhost:8000',
        region: process.env.REACT_APP_AWS_REGION || 'us-east-1'
      }
    }
  }
};

Amplify.configure(amplifyConfig);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);