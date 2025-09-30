import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Authenticator, useAuthenticator, View, Image, Text, Heading, Card } from '@aws-amplify/ui-react';
import { signUp } from 'aws-amplify/auth';
import '@aws-amplify/ui-react/styles.css';

import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import UploadPage from './components/UploadPage';
import JobsPage from './components/JobsPage';
import ApprovalPage from './components/ApprovalPage';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#6a37b0', // Eventual's primary color
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Simple approach: modify the form fields to include both username and email
// but provide clear instructions to users
const formFields = {
  signIn: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
    }
  },
  signUp: {
    username: {
      placeholder: 'Create a username (letters and numbers only)',
      label: 'Username',
      order: 1,
    },
    email: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
      isRequired: true,
      order: 2,
    }
  }
};

// Custom CSS to center the authenticator and apply Eventual's branding
const authenticatorStyles = `
  .amplify-authenticator {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 100vh !important;
    width: 100vw !important;
    background-color: #f5f5f5;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
  }
  
  .amplify-authenticator__form {
    max-width: 400px !important;
    width: 100% !important;
    margin: 0 auto !important;
    background: white !important;
    padding: 2rem !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    position: relative !important;
  }
  
  .amplify-tabs {
    background-color: white !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    padding: 2rem !important;
    margin: 0 !important;
  }
  
  /* Add helper text for the signup form */
  .amplify-tabs__panel[data-value="sign-up"]::before {
    content: "📝 To create an account: choose a username (letters/numbers only), then add your email address.";
    display: block;
    background-color: #e8f4fd;
    border: 1px solid #6a37b0;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #333;
    text-align: center;
  }
  
  /* Style for UNSELECTED tabs - 30% lighter than #6a37b0 */
  .amplify-tabs__item {
    color: #a988cc !important; /* 30% lighter than #6a37b0 */
    transition: color 0.2s ease !important;
  }
  
  /* Style for ACTIVE/SELECTED tabs */
  .amplify-tabs__item[data-state="active"] {
    color: #6a37b0 !important;
    border-bottom-color: #6a37b0 !important;
    font-weight: 600 !important;
  }
  
  /* Hover state for tabs */
  .amplify-tabs__item:hover {
    color: #6a37b0 !important;
  }
  
  /* Primary buttons styling */
  .amplify-button[data-variation="primary"],
  .amplify-button--primary {
    background-color: #6a37b0 !important;
    border-color: #6a37b0 !important;
  }
  
  .amplify-button[data-variation="primary"]:hover,
  .amplify-button--primary:hover {
    background-color: #5a2d96 !important;
    border-color: #5a2d96 !important;
  }
  
  /* "Forgot your password?" link styling */
  .amplify-button[data-variation="link"],
  .amplify-link,
  .amplify-button--link {
    color: #6a37b0 !important;
    text-decoration: none !important;
  }
  
  .amplify-button[data-variation="link"]:hover,
  .amplify-link:hover,
  .amplify-button--link:hover {
    color: #5a2d96 !important;
    text-decoration: underline !important;
  }
  
  /* Input focus styling */
  .amplify-input:focus {
    border-color: #6a37b0 !important;
    box-shadow: 0 0 0 2px rgba(106, 55, 176, 0.2) !important;
  }
  
  /* Ensure proper centering on all screen sizes */
  @media (max-width: 768px) {
    .amplify-authenticator__form {
      max-width: 90% !important;
      padding: 1.5rem !important;
    }
    
    .amplify-tabs {
      padding: 1.5rem !important;
    }
  }
  
  /* Remove any margin/padding that might interfere with centering */
  .amplify-authenticator > * {
    margin: 0 !important;
  }
`;

function App() {
  // Inject custom styles
  React.useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = authenticatorStyles;
    document.head.appendChild(styleElement);
    
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Authenticator formFields={formFields}>
        {({ signOut, user }) => (
          <Router>
            <Layout user={user} signOut={signOut}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<UploadPage />} />
                <Route path="/jobs" element={<JobsPage />} />
                <Route path="/approvals" element={<ApprovalPage />} />
              </Routes>
            </Layout>
          </Router>
        )}
      </Authenticator>
    </ThemeProvider>
  );
}

export default App;