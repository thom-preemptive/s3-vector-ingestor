import { fetchAuthSession } from 'aws-amplify/auth';

// Get the API endpoint from environment variables
const API_ENDPOINT = process.env.REACT_APP_API_URL || 'https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev';

// Helper function to get auth headers
const getAuthHeaders = async (): Promise<Record<string, string>> => {
  try {
    const session = await fetchAuthSession();
    console.log('Auth session:', session);
    const token = session.tokens?.idToken?.toString();
    console.log('ID Token retrieved:', token ? 'Yes (length: ' + token.length + ')' : 'No');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
    }
  } catch (error) {
    console.error('Error getting auth token:', error);
  }
  
  // Return headers without auth if token not available
  console.warn('No auth token available, returning headers without Authorization');
  return {
    'Content-Type': 'application/json'
  };
};

// API service functions
export const apiService = {
  // Health check
  async health() {
    try {
      const response = await fetch(`${API_ENDPOINT}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },

  // Dashboard endpoints
  async getDashboardJobs(limit = 20) {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/dashboard/jobs?limit=${limit}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching dashboard jobs:', error);
      // Return mock data for development
      return {
        jobs: [
          {
            id: '1',
            title: 'Sample Document Upload',
            status: 'completed',
            type: 'document',
            created: new Date().toISOString(),
            updated: new Date().toISOString()
          }
        ]
      };
    }
  },

  async getQueueStats() {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/dashboard/queues`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching queue stats:', error);
      // Return mock data for development
      return {
        processing: 2,
        completed: 15,
        failed: 1,
        pending: 3
      };
    }
  },

  // Jobs endpoints
  async getJobs() {
    try {
      console.log('getJobs: Fetching from', `${API_ENDPOINT}/jobs`);
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/jobs`, {
        headers
      });
      
      console.log('getJobs: Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('getJobs: Error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('getJobs: Success! Jobs count:', result.jobs?.length || 0);
      return result;
    } catch (error) {
      console.error('getJobs: Caught error:', error);
      // Return mock data for development
      return {
        jobs: [
          {
            id: '1',
            title: 'Document Upload Job',
            status: 'completed',
            type: 'document',
            created: new Date().toISOString(),
            notes: 'Successfully processed document upload'
          },
          {
            id: '2',
            title: 'URL Scraping Job',
            status: 'processing',
            type: 'url',
            created: new Date().toISOString(),
            notes: 'Processing URL content extraction'
          }
        ]
      };
    }
  },

  // Upload document using presigned S3 URLs (bypasses API Gateway 10MB limit)
  async uploadDocument(formData: FormData) {
    try {
      console.log('uploadDocument: Starting upload process');
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      console.log('uploadDocument: Token retrieved:', token ? 'Yes (length: ' + token.length + ')' : 'No');
      
      // Extract files and metadata from FormData
      const files: File[] = [];
      const jobName = formData.get('job_name') as string;
      const approvalRequired = formData.get('approval_required') === 'true';
      
      // Get all files from FormData
      const fileEntries = formData.getAll('files');
      for (const entry of fileEntries) {
        if (entry instanceof File) {
          files.push(entry);
        }
      }
      
      console.log(`uploadDocument: Uploading ${files.length} files via S3 presigned URLs`);
      
      // Step 1: Get presigned URLs for each file
      const uploadedFiles = [];
      for (const file of files) {
        // Get presigned URL
        const presignedResponse = await fetch(`${API_ENDPOINT}/upload/presigned-url`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          body: new URLSearchParams({
            filename: file.name,
            content_type: file.type || 'application/pdf'
          })
        });
        
        if (!presignedResponse.ok) {
          throw new Error(`Failed to get presigned URL: ${presignedResponse.status}`);
        }
        
        const { upload_url, file_key } = await presignedResponse.json();
        console.log(`uploadDocument: Got presigned URL for ${file.name}`);
        
        // Step 2: Upload file directly to S3
        const s3Response = await fetch(upload_url, {
          method: 'PUT',
          headers: {
            'Content-Type': file.type || 'application/pdf'
          },
          body: file
        });
        
        if (!s3Response.ok) {
          throw new Error(`Failed to upload ${file.name} to S3: ${s3Response.status}`);
        }
        
        console.log(`uploadDocument: Successfully uploaded ${file.name} to S3`);
        
        uploadedFiles.push({
          file_key,
          filename: file.name
        });
      }
      
      // Step 3: Trigger backend processing
      console.log('uploadDocument: Triggering backend processing');
      const processResponse = await fetch(`${API_ENDPOINT}/upload/process-s3-files`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          files: uploadedFiles,
          job_name: jobName,
          approval_required: approvalRequired
        })
      });
      
      console.log('uploadDocument: Process response status:', processResponse.status);
      
      if (!processResponse.ok) {
        const errorText = await processResponse.text();
        console.error('uploadDocument: Error response:', errorText);
        throw new Error(`HTTP error! status: ${processResponse.status}, body: ${errorText}`);
      }
      
      const result = await processResponse.json();
      console.log('uploadDocument: Success! Result:', result);
      return result;
    } catch (error) {
      console.error('uploadDocument: Caught error:', error);
      // Return mock success for development
      return {
        success: true,
        job_id: `mock-${Date.now()}`,
        status: 'pending',
        files_count: 0,
        message: 'Document upload simulation successful (mock data)'
      };
    }
  },

  // Submit URL for scraping
  async submitUrl(urlData: { url: string; notes?: string; approvalRequired?: boolean }) {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/process/urls`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          urls: [urlData.url],
          user_id: 'current-user',
          notes: urlData.notes || '',
          approval_required: urlData.approvalRequired || false
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error submitting URL:', error);
      // Return mock success for development
      return {
        success: true,
        job_id: `mock-url-${Date.now()}`,
        status: 'pending',
        message: 'URL submission simulation successful (mock data)'
      };
    }
  },

  // Approval endpoints
  async getPendingApprovals() {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/approvals/pending`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching pending approvals:', error);
      // Return mock data for development
      return {
        approvals: [
          {
            id: '1',
            title: 'Document Review Required',
            type: 'document',
            created: new Date().toISOString(),
            notes: 'Please review this document before processing'
          }
        ]
      };
    }
  },

  async approveItem(id: string, approved: boolean) {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/approvals/${id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ approved })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error updating approval:', error);
      // Return mock success for development
      return {
        success: true,
        message: 'Approval update simulation successful'
      };
    }
  },

  // Document viewing and search endpoints
  async listDocuments(limit = 50, offset = 0) {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/documents?limit=${limit}&offset=${offset}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error listing documents:', error);
      throw error;
    }
  },

  async getDocument(documentId: string) {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/documents/${documentId}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting document:', error);
      throw error;
    }
  },

  async searchDocuments(query: string, limit = 50) {
    try {
      const headers = await getAuthHeaders();
      const encodedQuery = encodeURIComponent(query);
      const response = await fetch(`${API_ENDPOINT}/documents/search?q=${encodedQuery}&limit=${limit}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error searching documents:', error);
      throw error;
    }
  },

  async getDocumentStats() {
    try {
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/documents/stats`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error getting document stats:', error);
      throw error;
    }
  },

  async downloadDocument(documentId: string, format: 'markdown' | 'json'): Promise<Blob> {
    try {
      const headers = await getAuthHeaders();
      // Remove Content-Type for file download
      delete headers['Content-Type'];
      
      const response = await fetch(`${API_ENDPOINT}/documents/${documentId}/download?format=${format}`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.blob();
    } catch (error) {
      console.error('Error downloading document:', error);
      throw error;
    }
  }
};

export default apiService;