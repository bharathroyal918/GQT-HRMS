import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { apiClient } from '../lib/apiClient';
import { User, LoginCredentials } from '../types/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<User>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  hasRole: (roleCode: string) => boolean;
  hasAnyRole: (roleCodes: string[]) => boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const checkAuth = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<User>('/auth/me/');
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (credentials: LoginCredentials): Promise<User> => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<{ user: User }>('/auth/login/', credentials);
      setUser(response.data.user);
      return response.data.user;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout/', {});
    } catch {
      // Ignore network failures on logout
    } finally {
      setUser(null);
    }
  };

  const hasRole = useCallback(
    (roleCode: string): boolean => {
      if (!user) return false;
      if (user.is_superuser || user.roles?.includes('ADMIN')) return true;
      return user.roles?.includes(roleCode) ?? false;
    },
    [user]
  );

  const hasAnyRole = useCallback(
    (roleCodes: string[]): boolean => {
      if (!user) return false;
      if (user.is_superuser || user.roles?.includes('ADMIN')) return true;
      return user.roles ? roleCodes.some((code) => user.roles.includes(code)) : false;
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        checkAuth,
        hasRole,
        hasAnyRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
