import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Authenticator } from '@aws-amplify/ui-react';
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

// Simplified form fields - email and password only  
const formFields = {
  signIn: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
    }
  },
  signUp: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
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
  }
  
  .amplify-tabs {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    padding: 2rem;
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