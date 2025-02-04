"use client";

import { createContext, useContext, useState, useEffect } from 'react';
import { 
  User,
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut,
  sendPasswordResetEmail
} from 'firebase/auth';
import { auth } from '@/app/lib/firebase';
import { useFirebase } from './FirebaseContext';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { user, loading } = useFirebase();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const checkAdminStatus = async () => {
      if (!user) return;
      try {
        const token = await user.getIdToken();
        const response = await fetch(`${API_URL}/users/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const userData = await response.json();
        setIsAdmin(userData.is_admin || false);
      } catch (error) {
        console.error('Error checking admin status:', error);
      }
    };

    checkAdminStatus();
  }, [user]);

  const signIn = async (email: string, password: string) => {
    try {
      console.log('AuthContext: Starting sign in for:', email);
      const result = await signInWithEmailAndPassword(auth, email, password);
      console.log('AuthContext: Sign in successful for:', result.user.email);
      
      // Get the ID token to set in cookies
      const idToken = await result.user.getIdToken();
      console.log('AuthContext: Got ID token, setting session cookie');
      
      // Set the token in a cookie
      const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: idToken }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to set session cookie');
      }

      // Try to create user in PostgreSQL (will not error if user already exists)
      try {
        await fetch(`${API_URL}/users/register`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${idToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ email })
        });
      } catch (error) {
        console.log('User record may already exist:', error);
      }
      
      console.log('AuthContext: Session cookie set successfully');
    } catch (error: any) {
      console.error('AuthContext: Sign in error:', error);
      throw new Error(error.message || 'Failed to sign in');
    }
  };

  const signUp = async (email: string, password: string) => {
    try {
      console.log('AuthContext: Starting sign up for:', email);
      const credential = await createUserWithEmailAndPassword(auth, email, password);
      console.log('AuthContext: Created auth account');
      
      // Get the ID token to set in cookies
      const idToken = await credential.user.getIdToken();
      console.log('AuthContext: Got ID token, setting session cookie');
      
      // Create user in PostgreSQL
      const userResponse = await fetch(`${API_URL}/users/register`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${idToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      });

      if (!userResponse.ok) {
        throw new Error('Failed to create user record');
      }
      
      // Set the token in a cookie
      const sessionResponse = await fetch('/api/auth/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: idToken }),
      });
      
      if (!sessionResponse.ok) {
        throw new Error('Failed to set session cookie');
      }
      
      console.log('AuthContext: Sign up complete');
    } catch (error: any) {
      console.error('AuthContext: Sign up error:', error);
      // If we fail after creating Firebase account, we should try to clean up
      if (auth.currentUser) {
        try {
          await auth.currentUser.delete();
        } catch (deleteError) {
          console.error('Failed to clean up Firebase account:', deleteError);
        }
      }
      throw new Error(error.message || 'Failed to create account');
    }
  };

  const logout = async () => {
    try {
      console.log('AuthContext: Starting logout');
      await signOut(auth);
      
      // Remove the session cookie
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
      });
      
      if (!response.ok) {
        throw new Error('Failed to clear session');
      }
      
      console.log('AuthContext: Logout complete');
    } catch (error: any) {
      console.error('AuthContext: Logout error:', error);
      throw new Error(error.message || 'Failed to log out');
    }
  };

  const resetPassword = async (email: string) => {
    try {
      console.log('AuthContext: Sending password reset email');
      await sendPasswordResetEmail(auth, email);
      console.log('AuthContext: Password reset email sent');
    } catch (error: any) {
      console.error('AuthContext: Password reset error:', error);
      throw new Error(error.message || 'Failed to send password reset email');
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      signIn, 
      signUp, 
      logout,
      resetPassword,
      isAdmin
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
