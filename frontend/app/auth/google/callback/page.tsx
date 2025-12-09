'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function GoogleCallbackPage() {
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { handleGoogleCallback } = useAuth();

  useEffect(() => {
    const code = searchParams.get('code');
    const errorParam = searchParams.get('error');

    if (errorParam) {
      setError('Google login was cancelled or failed');
      return;
    }

    if (!code) {
      setError('No authorization code received');
      return;
    }

    // Handle the callback
    handleGoogleCallback(code)
      .then(() => {
        router.push('/');
      })
      .catch((err) => {
        setError(err.message || 'Failed to complete Google login');
      });
  }, [searchParams, handleGoogleCallback, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-red/20 rounded-full mb-4">
            <AlertCircle className="w-8 h-8 text-accent-red" />
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">Login Failed</h1>
          <p className="text-dark-400 mb-6">{error}</p>
          <button
            onClick={() => router.push('/auth')}
            className="px-6 py-2 bg-accent-blue text-white rounded-lg hover:bg-accent-blue/90 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-accent-blue/20 rounded-full mb-4">
          <Sparkles className="w-8 h-8 text-accent-blue animate-pulse" />
        </div>
        <h1 className="text-xl font-semibold text-white mb-2">Completing Login...</h1>
        <p className="text-dark-400 mb-4">Please wait while we sign you in</p>
        <Loader2 className="w-6 h-6 text-accent-blue animate-spin mx-auto" />
      </div>
    </div>
  );
}


