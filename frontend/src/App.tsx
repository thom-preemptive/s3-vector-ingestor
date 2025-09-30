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
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background-color: #f5f5f5;
  }
  
  .amplify-authenticator__form {
    max-width: 400px;
    width: 100%;
    margin: 0 auto;
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
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
  
  /* Apply Eventual's primary color to active elements */
  .amplify-tabs__item[data-state="active"],
  .amplify-tabs__item:hover {
    color: #6a37b0 !important;
    border-bottom-color: #6a37b0 !important;
  }
  
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
  
  .amplify-button[data-variation="link"],
  .amplify-link {
    color: #6a37b0 !important;
  }
  
  .amplify-button[data-variation="link"]:hover,
  .amplify-link:hover {
    color: #5a2d96 !important;
  }
  
  .amplify-input:focus {
    border-color: #6a37b0 !important;
    box-shadow: 0 0 0 2px rgba(106, 55, 176, 0.2) !important;
  }
  
  .amplify-tabs {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 2rem;
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