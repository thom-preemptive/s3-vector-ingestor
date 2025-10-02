import React, { useState } from 'react';
import { Box, Paper, Typography, Button, Alert, CircularProgress, List, ListItem } from '@mui/material';
import { fetchAuthSession } from 'aws-amplify/auth';
import { Amplify } from 'aws-amplify';

interface DiagnosticResult {
  test: string;
  status: 'success' | 'error' | 'info';
  message: string;
  details?: any;
}

const DiagnosticPage: React.FC = () => {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [running, setRunning] = useState(false);

  const addResult = (result: DiagnosticResult) => {
    setResults(prev => [...prev, result]);
  };

  const runDiagnostics = async () => {
    setResults([]);
    setRunning(true);

    try {
      // Test 1: Check Amplify Configuration
      addResult({
        test: '1. Amplify Configuration',
        status: 'info',
        message: 'Checking Amplify configuration...',
        details: {
          Auth: Amplify.getConfig().Auth,
          API: Amplify.getConfig().API
        }
      });

      // Test 2: Check Environment Variables
      const apiUrl = process.env.REACT_APP_API_URL;
      const userPoolId = process.env.REACT_APP_COGNITO_USER_POOL_ID;
      const clientId = process.env.REACT_APP_COGNITO_CLIENT_ID;

      addResult({
        test: '2. Environment Variables',
        status: apiUrl && userPoolId && clientId ? 'success' : 'error',
        message: apiUrl && userPoolId && clientId ? 'All env vars present' : 'Missing env vars',
        details: {
          REACT_APP_API_URL: apiUrl || 'MISSING',
          REACT_APP_COGNITO_USER_POOL_ID: userPoolId || 'MISSING',
          REACT_APP_COGNITO_CLIENT_ID: clientId || 'MISSING'
        }
      });

      // Test 3: Fetch Auth Session
      let token: string | undefined;
      try {
        const session = await fetchAuthSession();
        token = session.tokens?.idToken?.toString();
        
        addResult({
          test: '3. Auth Session',
          status: token ? 'success' : 'error',
          message: token ? `Token retrieved (length: ${token.length})` : 'No token available',
          details: {
            hasTokens: !!session.tokens,
            hasIdToken: !!session.tokens?.idToken,
            hasAccessToken: !!session.tokens?.accessToken,
            tokenLength: token?.length
          }
        });
      } catch (error: any) {
        addResult({
          test: '3. Auth Session',
          status: 'error',
          message: 'Failed to get auth session',
          details: { error: error.message }
        });
      }

      // Test 4: Backend Health Check (no auth required)
      try {
        const healthResponse = await fetch(`${apiUrl}/health`);
        const healthData = await healthResponse.json();
        
        addResult({
          test: '4. Backend Health Check',
          status: healthResponse.ok ? 'success' : 'error',
          message: healthResponse.ok ? 'Backend is reachable' : `Backend returned ${healthResponse.status}`,
          details: {
            status: healthResponse.status,
            data: healthData,
            url: `${apiUrl}/health`
          }
        });
      } catch (error: any) {
        addResult({
          test: '4. Backend Health Check',
          status: 'error',
          message: 'Cannot reach backend',
          details: { 
            error: error.message,
            url: `${apiUrl}/health`
          }
        });
      }

      // Test 5: Authenticated API Call - /jobs endpoint
      if (token) {
        try {
          const jobsResponse = await fetch(`${apiUrl}/jobs`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          
          const responseText = await jobsResponse.text();
          let jobsData;
          try {
            jobsData = JSON.parse(responseText);
          } catch {
            jobsData = responseText;
          }

          addResult({
            test: '5. Authenticated API Call (/jobs)',
            status: jobsResponse.ok ? 'success' : 'error',
            message: jobsResponse.ok 
              ? `Success! ${jobsData.jobs?.length || 0} jobs returned`
              : `Failed with status ${jobsResponse.status}`,
            details: {
              status: jobsResponse.status,
              statusText: jobsResponse.statusText,
              headers: Object.fromEntries(jobsResponse.headers.entries()),
              response: jobsData,
              url: `${apiUrl}/jobs`
            }
          });
        } catch (error: any) {
          addResult({
            test: '5. Authenticated API Call (/jobs)',
            status: 'error',
            message: 'Request failed',
            details: { 
              error: error.message,
              name: error.name,
              url: `${apiUrl}/jobs`
            }
          });
        }
      } else {
        addResult({
          test: '5. Authenticated API Call (/jobs)',
          status: 'error',
          message: 'Skipped - no token available',
          details: {}
        });
      }

      // Test 6: CORS Preflight Check
      try {
        const corsResponse = await fetch(`${apiUrl}/health`, {
          method: 'OPTIONS'
        });
        
        addResult({
          test: '6. CORS Preflight',
          status: corsResponse.ok ? 'success' : 'error',
          message: corsResponse.ok ? 'CORS properly configured' : `CORS check returned ${corsResponse.status}`,
          details: {
            status: corsResponse.status,
            'Access-Control-Allow-Origin': corsResponse.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': corsResponse.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': corsResponse.headers.get('Access-Control-Allow-Headers')
          }
        });
      } catch (error: any) {
        addResult({
          test: '6. CORS Preflight',
          status: 'error',
          message: 'CORS check failed',
          details: { error: error.message }
        });
      }

    } catch (error: any) {
      addResult({
        test: 'Diagnostics',
        status: 'error',
        message: 'Unexpected error during diagnostics',
        details: { error: error.message }
      });
    } finally {
      setRunning(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        System Diagnostics
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        This page runs comprehensive tests to identify authentication and API connectivity issues.
      </Typography>

      <Button 
        variant="contained" 
        onClick={runDiagnostics} 
        disabled={running}
        sx={{ my: 2 }}
      >
        {running ? <CircularProgress size={24} /> : 'Run Diagnostics'}
      </Button>

      {results.length > 0 && (
        <Paper sx={{ p: 2, mt: 2 }}>
          <List>
            {results.map((result, index) => (
              <ListItem key={index} sx={{ display: 'block', mb: 2 }}>
                <Alert severity={result.status} sx={{ mb: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {result.test}
                  </Typography>
                  <Typography variant="body2">
                    {result.message}
                  </Typography>
                </Alert>
                {result.details && (
                  <Paper variant="outlined" sx={{ p: 1, mt: 1, bgcolor: 'grey.50' }}>
                    <pre style={{ 
                      fontSize: '11px', 
                      overflow: 'auto', 
                      margin: 0,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {JSON.stringify(result.details, null, 2)}
                    </pre>
                  </Paper>
                )}
              </ListItem>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
};

export default DiagnosticPage;
