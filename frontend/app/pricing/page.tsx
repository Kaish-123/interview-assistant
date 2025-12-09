'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, Sparkles, Zap, Crown, Building2, ArrowRight } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    description: 'Perfect for trying out Interview Assistant',
    icon: Sparkles,
    color: 'text-dark-300',
    bgColor: 'bg-dark-800',
    features: [
      '20 messages per day',
      '5 chat sessions',
      '2 document uploads',
      'GPT-4o Mini model',
      'Basic prompt templates',
    ],
    limitations: [
      'Limited chat history',
      'No priority support',
    ],
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 9.99,
    description: 'Great for regular interview preparation',
    icon: Zap,
    color: 'text-accent-blue',
    bgColor: 'bg-accent-blue/10',
    popular: false,
    features: [
      '100 messages per day',
      '50 chat sessions',
      '20 document uploads',
      'GPT-4o & GPT-4o Mini',
      'All prompt templates',
      'Chat history export',
    ],
    limitations: [],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 29.99,
    description: 'Best for serious job seekers',
    icon: Crown,
    color: 'text-accent-amber',
    bgColor: 'bg-accent-amber/10',
    popular: true,
    features: [
      'Unlimited messages',
      'Unlimited chat sessions',
      'Unlimited document uploads',
      'All AI models including GPT-4 Turbo',
      'Priority support',
      'Custom prompt templates',
      'Advanced analytics',
      'Interview tracking',
    ],
    limitations: [],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 99.99,
    description: 'For teams and organizations',
    icon: Building2,
    color: 'text-accent-purple',
    bgColor: 'bg-accent-purple/10',
    features: [
      'Everything in Pro',
      'Team management',
      'API access',
      'Custom integrations',
      'Dedicated support',
      'SLA guarantee',
      'White-label options',
      'Custom AI training',
    ],
    limitations: [],
  },
];

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();

  const getPrice = (price: number) => {
    if (billingCycle === 'yearly') {
      return (price * 10).toFixed(2); // 2 months free
    }
    return price.toFixed(2);
  };

  const handleSelectPlan = (planId: string) => {
    if (!isAuthenticated) {
      router.push(`/auth?redirect=/pricing&plan=${planId}`);
      return;
    }
    
    // In production, this would initiate payment
    alert(`Selected plan: ${planId}. Payment integration coming soon!`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark-950 to-dark-900">
      {/* Header */}
      <header className="border-b border-dark-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <button 
            onClick={() => router.push('/')}
            className="flex items-center gap-2 text-white font-semibold"
          >
            <Sparkles className="w-6 h-6 text-accent-blue" />
            Interview Assistant
          </button>
          {isAuthenticated ? (
            <div className="flex items-center gap-4">
              <span className="text-dark-400 text-sm">{user?.email}</span>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-accent-blue/90 transition-colors"
              >
                Go to App
              </button>
            </div>
          ) : (
            <button
              onClick={() => router.push('/auth')}
              className="px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-accent-blue/90 transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
      </header>

      {/* Hero */}
      <section className="py-16 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-dark-400 max-w-2xl mx-auto mb-8">
          Ace your interviews with AI-powered preparation. Choose the plan that fits your needs.
        </p>

        {/* Billing Toggle */}
        <div className="inline-flex items-center gap-4 p-1 bg-dark-800 rounded-xl">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all",
              billingCycle === 'monthly'
                ? "bg-accent-blue text-white"
                : "text-dark-400 hover:text-white"
            )}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={cn(
              "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
              billingCycle === 'yearly'
                ? "bg-accent-blue text-white"
                : "text-dark-400 hover:text-white"
            )}
          >
            Yearly
            <span className="px-2 py-0.5 bg-accent-green/20 text-accent-green text-xs rounded-full">
              Save 17%
            </span>
          </button>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-4 pb-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {PLANS.map((plan) => {
            const Icon = plan.icon;
            const isCurrentPlan = user?.subscription_tier === plan.id;
            
            return (
              <div
                key={plan.id}
                className={cn(
                  "relative bg-dark-800 rounded-2xl border p-6 flex flex-col",
                  plan.popular
                    ? "border-accent-amber shadow-lg shadow-accent-amber/10"
                    : "border-dark-700"
                )}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-1 bg-accent-amber text-dark-900 text-xs font-semibold rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Header */}
                <div className={cn("w-12 h-12 rounded-xl flex items-center justify-center mb-4", plan.bgColor)}>
                  <Icon className={cn("w-6 h-6", plan.color)} />
                </div>
                
                <h3 className="text-xl font-bold text-white mb-1">{plan.name}</h3>
                <p className="text-sm text-dark-400 mb-4">{plan.description}</p>

                {/* Price */}
                <div className="mb-6">
                  <span className="text-4xl font-bold text-white">${getPrice(plan.price)}</span>
                  {plan.price > 0 && (
                    <span className="text-dark-400">
                      /{billingCycle === 'yearly' ? 'year' : 'month'}
                    </span>
                  )}
                </div>

                {/* Features */}
                <ul className="space-y-3 flex-1">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-5 h-5 text-accent-green flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-dark-300">{feature}</span>
                    </li>
                  ))}
                  {plan.limitations.map((limitation, i) => (
                    <li key={i} className="flex items-start gap-2 opacity-50">
                      <span className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                        ✕
                      </span>
                      <span className="text-sm text-dark-400">{limitation}</span>
                    </li>
                  ))}
                </ul>

                {/* CTA */}
                <button
                  onClick={() => handleSelectPlan(plan.id)}
                  disabled={isCurrentPlan}
                  className={cn(
                    "mt-6 w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2",
                    isCurrentPlan
                      ? "bg-dark-700 text-dark-400 cursor-not-allowed"
                      : plan.popular
                        ? "bg-accent-amber text-dark-900 hover:bg-accent-amber/90"
                        : "bg-dark-700 text-white hover:bg-dark-600"
                  )}
                >
                  {isCurrentPlan ? (
                    'Current Plan'
                  ) : plan.price === 0 ? (
                    'Get Started Free'
                  ) : (
                    <>
                      Subscribe Now
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-3xl mx-auto px-4 pb-20">
        <h2 className="text-2xl font-bold text-white text-center mb-8">
          Frequently Asked Questions
        </h2>
        
        <div className="space-y-4">
          {[
            {
              q: 'Can I upgrade or downgrade my plan?',
              a: 'Yes, you can change your plan at any time. Upgrades take effect immediately, and downgrades apply at the end of your billing cycle.',
            },
            {
              q: 'What payment methods do you accept?',
              a: 'We accept all major credit cards, debit cards, and UPI payments through our secure payment partner.',
            },
            {
              q: 'Is there a free trial?',
              a: 'Our Free plan lets you try Interview Assistant without any payment. Upgrade when you need more features!',
            },
            {
              q: 'Can I cancel my subscription?',
              a: 'Yes, you can cancel anytime. You\'ll retain access to your plan until the end of your billing period.',
            },
          ].map((faq, i) => (
            <div key={i} className="bg-dark-800 rounded-xl p-6 border border-dark-700">
              <h3 className="font-semibold text-white mb-2">{faq.q}</h3>
              <p className="text-dark-400 text-sm">{faq.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-dark-500 text-sm">
            © 2024 TechYera. All rights reserved. | 
            <a href="/terms" className="text-accent-blue hover:underline ml-2">Terms</a> | 
            <a href="/privacy" className="text-accent-blue hover:underline ml-2">Privacy</a>
          </p>
        </div>
      </footer>
    </div>
  );
}


