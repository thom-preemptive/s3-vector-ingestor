import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Authenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import UploadPage from './components/UploadPage';
import URLScrapingPage from './components/URLScrapingPage';
import JobsPage from './components/JobsPage';
import ApprovalPage from './components/ApprovalPage';
import DiagnosticPage from './components/DiagnosticPage';
import DocumentsPage from './components/DocumentsPage';
import DocumentViewerPage from './components/DocumentViewerPage';
import SettingsPage from './components/SettingsPage';

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

// Simplified form fields - now truly email-only since Cognito uses email as username
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
  
  /* Style for UNSELECTED tabs - 30% lighter than #6a37b0 */
  .amplify-tabs__item {
    color: #a988cc !important; /* 30% lighter than #6a37b0 */
    transition: color 0.2s ease !important;
    border-bottom: 5px solid transparent !important;
  }
  
  /* Style for ACTIVE/SELECTED tabs */
  .amplify-tabs__item[data-state="active"] {
    color: #6a37b0 !important;
    border-bottom: 5px solid #6a37b0 !important;
    border-bottom-color: #6a37b0 !important;
    font-weight: 600 !important;
  }
  
  /* Ensure tab underline styling takes priority */
  .amplify-tabs__item[data-state="active"]::after {
    border-bottom: 5px solid #6a37b0 !important;
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
                <Route path="/upload" element={<UploadPage user={user} />} />
                <Route path="/url-scraping" element={<URLScrapingPage user={user} />} />
                <Route path="/jobs" element={<JobsPage />} />
                <Route path="/approvals" element={<ApprovalPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/diagnostics" element={<DiagnosticPage />} />
                <Route path="/documents" element={<DocumentsPage />} />
                <Route path="/documents/:documentId" element={<DocumentViewerPage />} />
              </Routes>
            </Layout>
          </Router>
        )}
      </Authenticator>
    </ThemeProvider>
  );
}

export default App;