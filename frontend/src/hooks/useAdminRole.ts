import { useEffect, useState } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

/**
 * Interface for admin permissions
 * Defines what administrative actions a user can perform
 */
export interface AdminPermissions {
  isAdmin: boolean;
  canClearTables: boolean;
  canClearBuckets: boolean;
  canViewAllUsers: boolean;
  canManageUsers: boolean;
  canViewSystemAnalytics: boolean;
  environment: string;
}

/**
 * Custom hook to check admin role and permissions
 * Reads from Cognito groups (cognito:groups in JWT token)
 * 
 * @returns AdminPermissions object with role-based permissions
 */
export const useAdminRole = (): AdminPermissions => {
  const [permissions, setPermissions] = useState<AdminPermissions>({
    isAdmin: false,
    canClearTables: false,
    canClearBuckets: false,
    canViewAllUsers: false,
    canManageUsers: false,
    canViewSystemAnalytics: false,
    environment: process.env.REACT_APP_ENVIRONMENT || 'dev'
  });

  useEffect(() => {
    /**
     * Check if current user has admin privileges via Cognito groups
     */
    const checkAdminRole = async (): Promise<void> => {
      try {
        // Get current authentication session
        const session = await fetchAuthSession();
        const groups = session.tokens?.accessToken?.payload['cognito:groups'] as string[] || [];
        
        // Check if user is in Administrators group
        const isAdmin = groups.includes('Administrators');
        const environment = process.env.REACT_APP_ENVIRONMENT || 'dev';
        const isMainEnvironment = environment === 'main';

        setPermissions({
          isAdmin,
          canClearTables: isAdmin && !isMainEnvironment,
          canClearBuckets: isAdmin && !isMainEnvironment,
          canViewAllUsers: isAdmin,
          canManageUsers: isAdmin,
          canViewSystemAnalytics: isAdmin,
          environment
        });
      } catch (error) {
        console.error('Error checking admin role:', error);
        // Set safe defaults on error
        setPermissions({
          isAdmin: false,
          canClearTables: false,
          canClearBuckets: false,
          canViewAllUsers: false,
          canManageUsers: false,
          canViewSystemAnalytics: false,
          environment: process.env.REACT_APP_ENVIRONMENT || 'dev'
        });
      }
    };

    checkAdminRole();
  }, []);

  return permissions;
};

export default useAdminRole;