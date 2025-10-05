import { useEffect, useState } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

/**
 * Custom hook to check admin role and permissions
 * Reads from Cognito custom:role attribute
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

export const useAdminRole = (): AdminPermissions => {
  const [permissions, setPermissions] = useState<AdminPermissions>({
    isAdmin: false,
    canClearTables: false,
    canClearBuckets: false,
    canViewAllUsers: false,
    canManageUsers: false,
    canViewSystemAnalytics: false,
    environment: 'unknown'
  });

  useEffect(() => {
    const checkAdminRole = async (): Promise<void> => {
      try {
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken;
        const environment = process.env.REACT_APP_ENVIRONMENT || 'unknown';
        
        if (!idToken) {
          return;
        }

        // Parse the JWT token to get custom attributes
        const payload = idToken.payload;
        const customRole = payload['custom:role'] as string;
        const isAdmin = customRole === 'admin';

        // Admin permissions based on environment
        const isNonProd = ['dev', 'test'].includes(environment);

        setPermissions({
          isAdmin,
          canClearTables: isAdmin && isNonProd,
          canClearBuckets: isAdmin && isNonProd,
          canViewAllUsers: isAdmin,
          canManageUsers: isAdmin,
          canViewSystemAnalytics: isAdmin,
          environment
        });
      } catch (error) {
        console.error('Error checking admin role:', error);
      }
    };

    checkAdminRole();
  }, []);

  return permissions;
};

export default useAdminRole;