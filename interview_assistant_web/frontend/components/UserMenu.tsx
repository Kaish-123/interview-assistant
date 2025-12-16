'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  User, 
  LogOut, 
  Settings, 
  CreditCard, 
  Crown,
  ChevronDown,
  Sparkles
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const TIER_COLORS = {
  free: 'bg-dark-600',
  starter: 'bg-accent-blue',
  pro: 'bg-accent-amber',
  enterprise: 'bg-accent-purple',
};

const TIER_LABELS = {
  free: 'Free',
  starter: 'Starter',
  pro: 'Pro',
  enterprise: 'Enterprise',
};

export default function UserMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!isAuthenticated || !user) {
    return (
      <button
        onClick={() => router.push('/auth')}
        className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-accent-blue/90 transition-colors text-sm font-medium"
      >
        <User className="w-4 h-4" />
        Sign In
      </button>
    );
  }

  const tier = user.subscription_tier as keyof typeof TIER_COLORS;

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 pr-3 bg-dark-800 rounded-lg hover:bg-dark-700 transition-colors border border-dark-700"
      >
        {/* Avatar */}
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt={user.full_name || user.email}
            className="w-8 h-8 rounded-lg object-cover"
          />
        ) : (
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <span className="text-white font-semibold text-sm">
              {(user.full_name || user.email)[0].toUpperCase()}
            </span>
          </div>
        )}
        
        {/* Name & Tier */}
        <div className="text-left hidden sm:block">
          <div className="text-sm font-medium text-dark-100 truncate max-w-[120px]">
            {user.full_name || user.email.split('@')[0]}
          </div>
          <div className="flex items-center gap-1">
            <span className={cn("w-1.5 h-1.5 rounded-full", TIER_COLORS[tier])} />
            <span className="text-xs text-dark-400">{TIER_LABELS[tier]}</span>
          </div>
        </div>
        
        <ChevronDown className={cn(
          "w-4 h-4 text-dark-400 transition-transform",
          isOpen && "rotate-180"
        )} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-dark-800 rounded-xl border border-dark-700 shadow-xl overflow-hidden z-50">
          {/* User Info */}
          <div className="p-4 border-b border-dark-700">
            <div className="font-medium text-white truncate">
              {user.full_name || 'User'}
            </div>
            <div className="text-sm text-dark-400 truncate">{user.email}</div>
            
            {/* Subscription Badge */}
            <div className={cn(
              "mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium",
              tier === 'free' ? 'bg-dark-700 text-dark-300' :
              tier === 'starter' ? 'bg-accent-blue/20 text-accent-blue' :
              tier === 'pro' ? 'bg-accent-amber/20 text-accent-amber' :
              'bg-accent-purple/20 text-accent-purple'
            )}>
              {tier === 'pro' || tier === 'enterprise' ? (
                <Crown className="w-3.5 h-3.5" />
              ) : (
                <Sparkles className="w-3.5 h-3.5" />
              )}
              {TIER_LABELS[tier]} Plan
            </div>
          </div>

          {/* Menu Items */}
          <div className="p-2">
            <button
              onClick={() => { setIsOpen(false); router.push('/settings'); }}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-dark-300 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
            
            <button
              onClick={() => { setIsOpen(false); router.push('/pricing'); }}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-dark-300 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
            >
              <CreditCard className="w-4 h-4" />
              {tier === 'free' ? 'Upgrade Plan' : 'Manage Subscription'}
            </button>
            
            <div className="my-2 h-px bg-dark-700" />
            
            <button
              onClick={async () => {
                setIsOpen(false);
                await logout();
                router.push('/auth');
              }}
              className="w-full flex items-center gap-3 px-3 py-2.5 text-sm text-accent-red hover:bg-accent-red/10 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}



