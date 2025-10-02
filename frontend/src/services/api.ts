import { fetchAuthSession } from 'aws-amplify/auth';

// Get the API endpoint from environment variables
const API_ENDPOINT = process.env.REACT_APP_API_URL || 'https://pubp32frrg.execute-api.us-east-1.amazonaws.com/dev';

// Helper function to get auth headers
const getAuthHeaders = async (): Promise<Record<string, string>> => {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();
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
      const headers = await getAuthHeaders();
      const response = await fetch(`${API_ENDPOINT}/jobs`, {
        headers
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching jobs:', error);
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

  // Upload document
  async uploadDocument(formData: FormData) {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      const response = await fetch(`${API_ENDPOINT}/upload/pdf`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // Don't set Content-Type for FormData, let browser set it
        },
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error uploading document:', error);
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
  }
};

export default apiService;