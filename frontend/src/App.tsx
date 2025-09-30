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
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Custom form fields configuration for email alias setup
const formFields = {
  signIn: {
    username: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
    }
  },
  signUp: {
    username: {
      placeholder: 'Enter a username (e.g., john_doe)',
      label: 'Username',
      order: 1,
    },
    email: {
      placeholder: 'Enter your email address',
      label: 'Email Address',
      isRequired: true,
      order: 2,
    },
    name: {
      placeholder: 'Enter your full name',
      label: 'Full Name',
      isRequired: true,
      order: 3,
    }
  }
};

function App() {
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