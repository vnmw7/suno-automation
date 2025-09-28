# Manual Login Fallback Integration Implementation

## Overview
This document contains the complete implementation for integrating manual login fallback for Google and Microsoft authentication in the Suno Automation system.

## Backend Implementation

### 1. Enhanced Authentication Service
**File:** `backend/services/auth_service.py`

```python
"""
System: Suno Automation
Module: Authentication Service
Purpose: Handle automated and manual authentication with fallback support
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, Literal
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback
from dotenv import load_dotenv

load_dotenv()

class AuthMethod(Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"
    SESSION = "session"

class AuthProvider(Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"

class AuthenticationService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_cache = {}
        self.max_retry_attempts = 3
        self.retry_delay = 2  # seconds

    async def authenticate(
        self,
        provider: AuthProvider,
        method: Optional[AuthMethod] = None,
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Main authentication entry point with fallback logic
        """
        # Try session first
        if self._check_valid_session(provider):
            return {
                "success": True,
                "method": AuthMethod.SESSION.value,
                "provider": provider.value,
                "message": "Using existing session"
            }

        # Try automated login first (if no method specified)
        if method is None or method == AuthMethod.AUTOMATED:
            result = await self._try_automated_login(provider)
            if result["success"]:
                return result
            self.logger.warning(f"Automated login failed for {provider.value}: {result.get('error')}")

        # Fallback to manual login
        if method == AuthMethod.MANUAL or credentials:
            result = await self._try_manual_login(provider, credentials)
            if result["success"]:
                self._store_session(provider, result.get("session_data"))
            return result

        return {
            "success": False,
            "error": "All authentication methods failed",
            "requires_manual": True
        }

    async def _try_automated_login(self, provider: AuthProvider) -> Dict[str, Any]:
        """
        Attempt automated login using environment credentials
        """
        try:
            if provider == AuthProvider.GOOGLE:
                from lib.login import login_google
                success = await login_google()
            elif provider == AuthProvider.MICROSOFT:
                from lib.login import suno_login_microsoft, login_google
                # Microsoft flow requires Google login first for email verification
                google_success = await login_google()
                if not google_success:
                    return {"success": False, "error": "Google login required for Microsoft auth failed"}
                success = await suno_login_microsoft()
            else:
                return {"success": False, "error": f"Unknown provider: {provider.value}"}

            return {
                "success": success,
                "method": AuthMethod.AUTOMATED.value,
                "provider": provider.value
            }
        except Exception as e:
            self.logger.error(f"Automated login error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _try_manual_login(
        self,
        provider: AuthProvider,
        credentials: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Attempt manual login with user-provided credentials
        """
        if not credentials:
            return {
                "success": False,
                "error": "Credentials required for manual login",
                "requires_input": True
            }

        try:
            if provider == AuthProvider.GOOGLE:
                result = await self._manual_google_login(
                    credentials.get("email"),
                    credentials.get("password")
                )
            elif provider == AuthProvider.MICROSOFT:
                result = await self._manual_microsoft_login(
                    credentials.get("email"),
                    credentials.get("password"),
                    credentials.get("verification_code")
                )
            else:
                return {"success": False, "error": f"Unknown provider: {provider.value}"}

            return {
                "success": result.get("success", False),
                "method": AuthMethod.MANUAL.value,
                "provider": provider.value,
                "session_data": result.get("session_data"),
                "requires_verification": result.get("requires_verification", False),
                "error": result.get("error")
            }
        except Exception as e:
            self.logger.error(f"Manual login error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _manual_google_login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Manual Google login implementation
        """
        from lib.login import AsyncCamoufox, config

        try:
            async with AsyncCamoufox(
                headless=False,
                persistent_context=True,
                user_data_dir="backend/camoufox_session_data",
                os=("windows"),
                config=config,
                humanize=True,
                i_know_what_im_doing=True,
            ) as browser:
                page = await browser.new_page()

                await page.goto("https://accounts.google.com/", wait_until="networkidle")

                # Check if already logged in
                if "myaccount.google.com" in page.url:
                    return {"success": True, "session_data": {"logged_in": True}}

                # Fill email
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.locator('input[type="email"]').fill(email)
                await page.click('button:has-text("Next")')

                # Fill password
                await page.wait_for_selector('input[type="password"]', timeout=10000)
                await page.locator('input[type="password"]').fill(password)
                await page.click('button:has-text("Next")')

                # Wait for redirect
                await page.wait_for_url("**/myaccount.google.com/**", timeout=30000)

                return {
                    "success": True,
                    "session_data": {
                        "logged_in": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }

        except Exception as e:
            self.logger.error(f"Manual Google login failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _manual_microsoft_login(
        self,
        email: str,
        password: str,
        verification_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manual Microsoft login implementation with 2FA support
        """
        from lib.login import AsyncCamoufox, config

        try:
            async with AsyncCamoufox(
                headless=False,
                persistent_context=True,
                user_data_dir="backend/camoufox_session_data",
                os=("windows"),
                config=config,
                humanize=True,
                i_know_what_im_doing=True,
            ) as browser:
                page = await browser.new_page()

                # Navigate to Suno
                await page.goto("https://suno.com")
                await page.wait_for_load_state("load", timeout=10000)

                # Check if already logged in
                if await page.locator('button:has(span:has-text("Create"))').is_visible(timeout=5000):
                    return {"success": True, "session_data": {"logged_in": True}}

                # Click sign in
                await page.click('button:has(span:has-text("Sign in"))')
                await page.click('button:has(img[alt="Sign in with Microsoft"])')

                # Enter email
                await page.wait_for_selector('input[type="email"]', timeout=10000)
                await page.locator('input[type="email"]').fill(email)
                await page.keyboard.press("Enter")

                # Handle 2FA if required
                if await page.locator('button:has-text("Send code")').is_visible(timeout=5000):
                    if not verification_code:
                        await page.click('button:has-text("Send code")')
                        return {
                            "success": False,
                            "requires_verification": True,
                            "message": "Verification code sent to email. Please provide the code."
                        }

                    # Enter verification code
                    for i, digit in enumerate(verification_code):
                        selector = f'input[id="codeEntry-{i}"]'
                        await page.wait_for_selector(selector, timeout=5000)
                        await page.fill(selector, digit)

                    await page.keyboard.press("Enter")

                # Wait for successful login
                await page.wait_for_selector('button:has(span:has-text("Create"))', timeout=30000)

                return {
                    "success": True,
                    "session_data": {
                        "logged_in": True,
                        "timestamp": datetime.now().isoformat()
                    }
                }

        except Exception as e:
            self.logger.error(f"Manual Microsoft login failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _check_valid_session(self, provider: AuthProvider) -> bool:
        """
        Check if there's a valid session for the provider
        """
        session = self.session_cache.get(provider.value)
        if not session:
            return False

        # Check session expiry (24 hours)
        if "timestamp" in session:
            session_time = datetime.fromisoformat(session["timestamp"])
            if datetime.now() - session_time > timedelta(hours=24):
                del self.session_cache[provider.value]
                return False

        return session.get("logged_in", False)

    def _store_session(self, provider: AuthProvider, session_data: Dict[str, Any]):
        """
        Store session information
        """
        if session_data:
            self.session_cache[provider.value] = session_data
            # Optionally persist to database or file
            self._persist_session(provider, session_data)

    def _persist_session(self, provider: AuthProvider, session_data: Dict[str, Any]):
        """
        Persist session to storage
        """
        try:
            session_file = f"backend/sessions/{provider.value}_session.json"
            os.makedirs("backend/sessions", exist_ok=True)
            with open(session_file, "w") as f:
                json.dump(session_data, f)
        except Exception as e:
            self.logger.error(f"Failed to persist session: {str(e)}")

    async def refresh_session(self, provider: AuthProvider) -> Dict[str, Any]:
        """
        Refresh authentication session
        """
        # Clear existing session
        if provider.value in self.session_cache:
            del self.session_cache[provider.value]

        # Re-authenticate
        return await self.authenticate(provider, method=AuthMethod.AUTOMATED)

    def get_session_status(self, provider: AuthProvider) -> Dict[str, Any]:
        """
        Get current session status
        """
        if self._check_valid_session(provider):
            session = self.session_cache.get(provider.value, {})
            return {
                "authenticated": True,
                "provider": provider.value,
                "timestamp": session.get("timestamp"),
                "valid": True
            }

        return {
            "authenticated": False,
            "provider": provider.value,
            "valid": False
        }

# Singleton instance
auth_service = AuthenticationService()
```

### 2. API Routes for Manual Authentication
**File:** `backend/api/auth/routes.py`

```python
"""
System: Suno Automation
Module: Authentication Routes
Purpose: API endpoints for manual login fallback
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from services.auth_service import auth_service, AuthProvider, AuthMethod

router = APIRouter(prefix="/api/v2/auth", tags=["authentication"])

class ManualLoginRequest(BaseModel):
    provider: str  # "google" or "microsoft"
    email: EmailStr
    password: str
    verification_code: Optional[str] = None

class AuthStatusResponse(BaseModel):
    authenticated: bool
    provider: Optional[str] = None
    valid: bool
    timestamp: Optional[str] = None

class LoginResponse(BaseModel):
    success: bool
    method: Optional[str] = None
    provider: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    requires_verification: bool = False
    requires_manual: bool = False

@router.post("/manual-login", response_model=LoginResponse)
async def manual_login(request: ManualLoginRequest):
    """
    Endpoint for manual login with user-provided credentials
    """
    try:
        provider = AuthProvider(request.provider.lower())
        credentials = {
            "email": request.email,
            "password": request.password,
            "verification_code": request.verification_code
        }

        result = await auth_service.authenticate(
            provider=provider,
            method=AuthMethod.MANUAL,
            credentials=credentials
        )

        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-code", response_model=LoginResponse)
async def verify_code(
    provider: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    verification_code: str = Body(...)
):
    """
    Submit verification code for 2FA
    """
    try:
        provider_enum = AuthProvider(provider.lower())
        credentials = {
            "email": email,
            "password": password,
            "verification_code": verification_code
        }

        result = await auth_service.authenticate(
            provider=provider_enum,
            method=AuthMethod.MANUAL,
            credentials=credentials
        )

        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(provider: str):
    """
    Check authentication status for a provider
    """
    try:
        provider_enum = AuthProvider(provider.lower())
        status = auth_service.get_session_status(provider_enum)
        return AuthStatusResponse(**status)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh", response_model=LoginResponse)
async def refresh_session(provider: str = Body(...)):
    """
    Refresh authentication session
    """
    try:
        provider_enum = AuthProvider(provider.lower())
        result = await auth_service.refresh_session(provider_enum)
        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(provider: str = Body(...)):
    """
    Clear session for a provider
    """
    try:
        provider_enum = AuthProvider(provider.lower())
        if provider_enum.value in auth_service.session_cache:
            del auth_service.session_cache[provider_enum.value]

        return {"success": True, "message": f"Logged out from {provider}"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-login", response_model=LoginResponse)
async def auto_login(provider: str = Body(...)):
    """
    Attempt automated login with environment credentials
    """
    try:
        provider_enum = AuthProvider(provider.lower())
        result = await auth_service.authenticate(
            provider=provider_enum,
            method=AuthMethod.AUTOMATED
        )
        return LoginResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Update Main Application
**File:** `backend/main.py` (additions)

```python
# Add to imports
from api.auth.routes import router as auth_router

# Add router (after existing routers)
app.include_router(auth_router)

# Update login endpoint to use new service
@app.get("/login")
async def login_endpoint():
    """
    Initiates the Suno login process with fallback support
    """
    from services.auth_service import auth_service, AuthProvider

    # Try automated login first, will fallback if needed
    result = await auth_service.authenticate(AuthProvider.MICROSOFT)
    return result

@app.get("/login/microsoft")
async def login_with_microsoft_endpoint():
    """
    Handles login using Microsoft credentials with fallback
    """
    from services.auth_service import auth_service, AuthProvider

    result = await auth_service.authenticate(AuthProvider.MICROSOFT)
    return result
```

## Frontend Implementation

### 1. Authentication Hook
**File:** `frontend/app/hooks/useAuth.ts`

```typescript
/**
 * System: Suno Automation
 * Module: Authentication Hook
 * Purpose: React hook for managing authentication state and operations
 */

import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../lib/api';

export type AuthProvider = 'google' | 'microsoft';
export type AuthMethod = 'automated' | 'manual' | 'session';

export interface AuthStatus {
  authenticated: boolean;
  provider?: string;
  valid: boolean;
  timestamp?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  verificationCode?: string;
}

export interface LoginResult {
  success: boolean;
  method?: string;
  provider?: string;
  message?: string;
  error?: string;
  requiresVerification?: boolean;
  requiresManual?: boolean;
}

export const useAuth = () => {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [requiresVerification, setRequiresVerification] = useState(false);

  // Check authentication status
  const checkAuthStatus = useCallback(async (provider: AuthProvider) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v2/auth/status?provider=${provider}`
      );
      const data: AuthStatus = await response.json();
      setAuthStatus(data);
      return data;
    } catch (err) {
      console.error('Failed to check auth status:', err);
      setError(err instanceof Error ? err.message : 'Failed to check auth status');
      return null;
    }
  }, []);

  // Automated login
  const autoLogin = useCallback(async (provider: AuthProvider) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v2/auth/auto-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider }),
      });

      const result: LoginResult = await response.json();

      if (result.success) {
        await checkAuthStatus(provider);
      } else if (result.requiresManual) {
        setError('Automated login failed. Please login manually.');
      }

      return result;
    } catch (err) {
      console.error('Auto login failed:', err);
      setError(err instanceof Error ? err.message : 'Auto login failed');
      return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
    } finally {
      setLoading(false);
    }
  }, [checkAuthStatus]);

  // Manual login
  const manualLogin = useCallback(async (
    provider: AuthProvider,
    credentials: LoginCredentials
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v2/auth/manual-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          email: credentials.email,
          password: credentials.password,
          verification_code: credentials.verificationCode,
        }),
      });

      const result: LoginResult = await response.json();

      if (result.success) {
        await checkAuthStatus(provider);
        setRequiresVerification(false);
      } else if (result.requiresVerification) {
        setRequiresVerification(true);
        setError('Please enter the verification code sent to your email.');
      } else {
        setError(result.error || 'Login failed');
      }

      return result;
    } catch (err) {
      console.error('Manual login failed:', err);
      setError(err instanceof Error ? err.message : 'Manual login failed');
      return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
    } finally {
      setLoading(false);
    }
  }, [checkAuthStatus]);

  // Submit verification code
  const submitVerificationCode = useCallback(async (
    provider: AuthProvider,
    email: string,
    password: string,
    verificationCode: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v2/auth/verify-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          email,
          password,
          verification_code: verificationCode,
        }),
      });

      const result: LoginResult = await response.json();

      if (result.success) {
        await checkAuthStatus(provider);
        setRequiresVerification(false);
      } else {
        setError(result.error || 'Verification failed');
      }

      return result;
    } catch (err) {
      console.error('Verification failed:', err);
      setError(err instanceof Error ? err.message : 'Verification failed');
      return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
    } finally {
      setLoading(false);
    }
  }, [checkAuthStatus]);

  // Refresh session
  const refreshSession = useCallback(async (provider: AuthProvider) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v2/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider }),
      });

      const result: LoginResult = await response.json();

      if (result.success) {
        await checkAuthStatus(provider);
      } else {
        setError(result.error || 'Session refresh failed');
      }

      return result;
    } catch (err) {
      console.error('Session refresh failed:', err);
      setError(err instanceof Error ? err.message : 'Session refresh failed');
      return { success: false, error: err instanceof Error ? err.message : 'Unknown error' };
    } finally {
      setLoading(false);
    }
  }, [checkAuthStatus]);

  // Logout
  const logout = useCallback(async (provider: AuthProvider) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v2/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider }),
      });

      const result = await response.json();

      if (result.success) {
        setAuthStatus(null);
      }

      return result;
    } catch (err) {
      console.error('Logout failed:', err);
      setError(err instanceof Error ? err.message : 'Logout failed');
      return { success: false };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    authStatus,
    loading,
    error,
    requiresVerification,
    checkAuthStatus,
    autoLogin,
    manualLogin,
    submitVerificationCode,
    refreshSession,
    logout,
  };
};
```

### 2. Authentication Modal Component
**File:** `frontend/app/components/auth/AuthModal.tsx`

```tsx
/**
 * System: Suno Automation
 * Module: Authentication Modal
 * Purpose: Modal component for manual login with Google/Microsoft
 */

import React, { useState } from 'react';
import { useAuth, AuthProvider } from '../../hooks/useAuth';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider?: AuthProvider;
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  provider: initialProvider,
  onSuccess,
}) => {
  const { manualLogin, submitVerificationCode, loading, error, requiresVerification } = useAuth();
  const [provider, setProvider] = useState<AuthProvider>(initialProvider || 'microsoft');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [step, setStep] = useState<'credentials' | 'verification'>('credentials');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (step === 'credentials') {
      const result = await manualLogin(provider, { email, password });

      if (result.success) {
        onSuccess?.();
        onClose();
      } else if (result.requiresVerification) {
        setStep('verification');
      }
    } else {
      const result = await submitVerificationCode(provider, email, password, verificationCode);

      if (result.success) {
        onSuccess?.();
        onClose();
      }
    }
  };

  const handleProviderChange = (newProvider: AuthProvider) => {
    setProvider(newProvider);
    setStep('credentials');
    setVerificationCode('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Manual Login</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Provider Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Provider
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => handleProviderChange('google')}
              className={`flex-1 py-2 px-4 rounded-md border ${
                provider === 'google'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Google
            </button>
            <button
              type="button"
              onClick={() => handleProviderChange('microsoft')}
              className={`flex-1 py-2 px-4 rounded-md border ${
                provider === 'microsoft'
                  ? 'bg-blue-500 text-white border-blue-500'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Microsoft
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          {step === 'credentials' ? (
            <>
              <div className="mb-4">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={loading}
                />
              </div>

              <div className="mb-4">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  disabled={loading}
                />
              </div>
            </>
          ) : (
            <div className="mb-4">
              <label htmlFor="verificationCode" className="block text-sm font-medium text-gray-700 mb-1">
                Verification Code
              </label>
              <input
                type="text"
                id="verificationCode"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter 6-digit code"
                maxLength={6}
                required
                disabled={loading}
              />
              <p className="text-sm text-gray-600 mt-1">
                Check your email for the verification code
              </p>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 py-2 px-4 border border-transparent rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? 'Loading...' : step === 'credentials' ? 'Login' : 'Verify'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
```

### 3. Authentication Status Component
**File:** `frontend/app/components/auth/AuthStatus.tsx`

```tsx
/**
 * System: Suno Automation
 * Module: Authentication Status
 * Purpose: Display current authentication status with quick actions
 */

import React, { useEffect, useState } from 'react';
import { useAuth, AuthProvider } from '../../hooks/useAuth';
import { AuthModal } from './AuthModal';

interface AuthStatusProps {
  provider: AuthProvider;
  onAuthChange?: (authenticated: boolean) => void;
}

export const AuthStatus: React.FC<AuthStatusProps> = ({ provider, onAuthChange }) => {
  const { authStatus, checkAuthStatus, autoLogin, refreshSession, logout } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    // Check auth status on mount
    checkAuthStatus(provider);
  }, [provider, checkAuthStatus]);

  useEffect(() => {
    // Notify parent of auth changes
    if (authStatus) {
      onAuthChange?.(authStatus.authenticated);
    }
  }, [authStatus, onAuthChange]);

  const handleAutoLogin = async () => {
    setIsChecking(true);
    const result = await autoLogin(provider);
    if (!result.success && result.requiresManual) {
      setShowModal(true);
    }
    setIsChecking(false);
  };

  const handleRefresh = async () => {
    setIsChecking(true);
    await refreshSession(provider);
    setIsChecking(false);
  };

  const handleLogout = async () => {
    await logout(provider);
  };

  const getStatusColor = () => {
    if (isChecking) return 'bg-yellow-100 text-yellow-800';
    if (authStatus?.authenticated) return 'bg-green-100 text-green-800';
    return 'bg-red-100 text-red-800';
  };

  const getStatusText = () => {
    if (isChecking) return 'Checking...';
    if (authStatus?.authenticated) return 'Authenticated';
    return 'Not Authenticated';
  };

  return (
    <>
      <div className="flex items-center gap-2 p-2 rounded-md bg-gray-50">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">
            {provider === 'google' ? 'Google' : 'Microsoft'}:
          </span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>

        <div className="flex gap-1 ml-auto">
          {!authStatus?.authenticated && (
            <>
              <button
                onClick={handleAutoLogin}
                className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                disabled={isChecking}
              >
                Auto Login
              </button>
              <button
                onClick={() => setShowModal(true)}
                className="px-3 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Manual Login
              </button>
            </>
          )}

          {authStatus?.authenticated && (
            <>
              <button
                onClick={handleRefresh}
                className="px-3 py-1 text-xs bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
                disabled={isChecking}
              >
                Refresh
              </button>
              <button
                onClick={handleLogout}
                className="px-3 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>

      <AuthModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        provider={provider}
        onSuccess={() => {
          setShowModal(false);
          checkAuthStatus(provider);
        }}
      />
    </>
  );
};
```

### 4. Integration with Existing Components
**File:** `frontend/app/components/BookCard.tsx` (additions)

```tsx
// Add to imports
import { AuthStatus } from './auth/AuthStatus';
import { useState } from 'react';

// Add to component (inside BookCard component, before the form)
const [isAuthenticated, setIsAuthenticated] = useState(false);

// Add authentication status display (add this before the song generation form)
<div className="mb-4">
  <AuthStatus
    provider="microsoft"
    onAuthChange={setIsAuthenticated}
  />
</div>

// Conditionally enable form based on authentication
{!isAuthenticated && (
  <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
    <p className="text-sm text-yellow-800">
      Please authenticate with Microsoft to generate songs.
    </p>
  </div>
)}

// Update form submit button to be disabled when not authenticated
<button
  type="submit"
  disabled={isLoading || !isAuthenticated}
  className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white
    ${isLoading || !isAuthenticated
      ? 'bg-gray-400 cursor-not-allowed'
      : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500'}`}
>
  {isLoading ? 'Generating...' : 'Generate Song'}
</button>
```

## Database Schema

### SQL Schema for Session Management
**File:** `backend/database_migration/tables/auth_sessions.sql`

```sql
-- Authentication sessions table
CREATE TABLE IF NOT EXISTS auth_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authentication attempts table for tracking
CREATE TABLE IF NOT EXISTS auth_attempts (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    method VARCHAR(50) NOT NULL,
    email VARCHAR(255),
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_auth_sessions_provider ON auth_sessions(provider);
CREATE INDEX idx_auth_sessions_email ON auth_sessions(email);
CREATE INDEX idx_auth_sessions_expires ON auth_sessions(expires_at);
CREATE INDEX idx_auth_attempts_provider ON auth_attempts(provider);
CREATE INDEX idx_auth_attempts_created ON auth_attempts(created_at);
```

## Environment Configuration

### Updated .env file structure
**File:** `backend/.env.example`

```env
# Existing Supabase configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Authentication Settings
AUTH_METHOD=automated  # Options: automated, manual, hybrid
AUTH_SESSION_TIMEOUT=86400  # 24 hours in seconds
AUTH_MAX_RETRY_ATTEMPTS=3
AUTH_RETRY_DELAY=2  # seconds

# Automated Login Credentials (optional if using manual mode)
GOOGLE_EMAIL=your_google_email
GOOGLE_PASSWORD=your_google_password
MICROSOFT_EMAIL=your_microsoft_email
MICROSOFT_PASSWORD=your_microsoft_password

# Security Settings
AUTH_ENCRYPTION_KEY=your_32_char_encryption_key_here
AUTH_RATE_LIMIT_REQUESTS=10
AUTH_RATE_LIMIT_WINDOW=60  # seconds
```

## Deployment Instructions

### 1. Backend Setup
```bash
# Install new dependencies
cd backend
pip install cryptography redis

# Run database migrations
python database_migration/migrate.py

# Create sessions directory
mkdir -p backend/sessions

# Update main.py to include auth router
# Start the backend server
python main.py
```

### 2. Frontend Setup
```bash
# Install dependencies (if any new ones)
cd frontend
npm install

# Update environment variables if needed
# Start the frontend
npm run dev
```

### 3. Configuration Steps
1. Update `.env` file with authentication settings
2. Choose authentication method (automated/manual/hybrid)
3. Configure session timeout and retry settings
4. Set up encryption key for secure credential storage

## Security Considerations

1. **Credential Storage**: Never store plaintext passwords. Use encryption for any stored credentials.
2. **Session Management**: Implement proper session expiry and refresh mechanisms.
3. **Rate Limiting**: Add rate limiting to prevent brute force attacks on manual login.
4. **HTTPS Only**: Ensure all authentication endpoints are accessed over HTTPS in production.
5. **CSRF Protection**: Implement CSRF tokens for state-changing operations.
6. **Input Validation**: Validate and sanitize all user inputs.
7. **Error Messages**: Don't expose sensitive information in error messages.
8. **Audit Logging**: Log all authentication attempts for security monitoring.

## Monitoring and Logging

### Key Metrics to Track
- Authentication success/failure rates by method
- Average authentication time
- Session duration and refresh rates
- Error types and frequencies
- Manual fallback usage percentage

### Log Format
```python
{
    "timestamp": "2024-01-26T10:30:00Z",
    "level": "INFO",
    "service": "auth",
    "provider": "microsoft",
    "method": "manual",
    "success": true,
    "duration_ms": 2500,
    "session_id": "xxx-xxx-xxx",
    "error": null
}
```

## Troubleshooting Guide

### Common Issues and Solutions

1. **Automated login fails**
   - Check environment variables are set correctly
   - Verify network connectivity
   - Check browser automation dependencies
   - Falls back to manual login automatically

2. **Verification code not received**
   - Check email spam folder
   - Verify email service is accessible
   - Retry after a few minutes
   - Use backup email if configured

3. **Session expires frequently**
   - Adjust AUTH_SESSION_TIMEOUT in .env
   - Check for clock synchronization issues
   - Verify refresh token mechanism is working

4. **Manual login not working**
   - Verify credentials are correct
   - Check if 2FA is enabled on the account
   - Ensure provider selection is correct
   - Check browser console for errors

## Future Enhancements

1. **OAuth 2.0 Integration**: Direct OAuth flow without browser automation
2. **Multi-factor Authentication**: Support for various 2FA methods
3. **Single Sign-On (SSO)**: Enterprise SSO integration
4. **Remember Me**: Persistent login across browser sessions
5. **Account Linking**: Link multiple providers to single account
6. **Biometric Authentication**: Support for fingerprint/face recognition
7. **Session Sharing**: Share sessions across multiple devices
8. **Backup Authentication**: Alternative authentication methods
```