'use client';

import { useState, useEffect } from 'react';
import { Download, Apple, MonitorPlay, CheckCircle, ExternalLink } from 'lucide-react';

const GITHUB_REPO = 'techyera/interview-assistant';
const LATEST_VERSION = '1.0.0';

interface ReleaseAsset {
  name: string;
  browser_download_url: string;
  size: number;
}

interface Release {
  tag_name: string;
  name: string;
  assets: ReleaseAsset[];
  published_at: string;
}

export default function DownloadPage() {
  const [release, setRelease] = useState<Release | null>(null);
  const [loading, setLoading] = useState(true);
  const [platform, setPlatform] = useState<'mac' | 'windows' | 'unknown'>('unknown');

  useEffect(() => {
    // Detect platform
    if (typeof navigator !== 'undefined') {
      const userAgent = navigator.userAgent.toLowerCase();
      if (userAgent.includes('mac')) {
        setPlatform('mac');
      } else if (userAgent.includes('win')) {
        setPlatform('windows');
      }
    }

    // Fetch latest release from GitHub
    fetchLatestRelease();
  }, []);

  const fetchLatestRelease = async () => {
    try {
      const response = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`);
      if (response.ok) {
        const data = await response.json();
        setRelease(data);
      }
    } catch (error) {
      console.error('Failed to fetch release:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDownloadUrl = (type: 'mac' | 'windows') => {
    if (release?.assets) {
      const asset = release.assets.find(a => 
        type === 'mac' 
          ? a.name.endsWith('.dmg') || a.name.includes('darwin')
          : a.name.endsWith('.exe') || a.name.includes('windows')
      );
      return asset?.browser_download_url;
    }
    return `https://github.com/${GITHUB_REPO}/releases/latest`;
  };

  const formatSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark-950 via-dark-900 to-dark-950">
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-accent-blue via-accent-purple to-accent-green bg-clip-text text-transparent mb-6">
            Download Interview Assistant
          </h1>
          <p className="text-xl text-dark-300 max-w-2xl mx-auto">
            AI-powered interview preparation tool with real-time transcription.
            Available for macOS and Windows.
          </p>
        </div>

        {/* Download Cards */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* macOS Card */}
          <div className={`relative bg-dark-800/50 rounded-2xl border ${platform === 'mac' ? 'border-accent-blue' : 'border-dark-700'} p-8 hover:border-accent-blue/50 transition-all group`}>
            {platform === 'mac' && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-accent-blue text-white text-xs font-medium rounded-full">
                Recommended for you
              </div>
            )}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-dark-700 rounded-2xl flex items-center justify-center">
                <Apple className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">macOS</h2>
                <p className="text-dark-400">macOS 10.15 or later</p>
              </div>
            </div>
            
            <ul className="space-y-3 mb-8">
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                Intel & Apple Silicon
              </li>
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                Native performance
              </li>
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                Global hotkeys support
              </li>
            </ul>

            <a
              href={getDownloadUrl('mac')}
              className="flex items-center justify-center gap-2 w-full py-4 bg-accent-blue hover:bg-accent-blue/90 text-white font-semibold rounded-xl transition-colors"
            >
              <Download className="w-5 h-5" />
              Download for macOS
            </a>
            <p className="text-center text-dark-500 text-sm mt-3">
              Version {release?.tag_name?.replace('v', '') || LATEST_VERSION} • DMG installer
            </p>
          </div>

          {/* Windows Card */}
          <div className={`relative bg-dark-800/50 rounded-2xl border ${platform === 'windows' ? 'border-accent-blue' : 'border-dark-700'} p-8 hover:border-accent-blue/50 transition-all group`}>
            {platform === 'windows' && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-accent-blue text-white text-xs font-medium rounded-full">
                Recommended for you
              </div>
            )}
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-dark-700 rounded-2xl flex items-center justify-center">
                <MonitorPlay className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Windows</h2>
                <p className="text-dark-400">Windows 10 or later</p>
              </div>
            </div>
            
            <ul className="space-y-3 mb-8">
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                64-bit support
              </li>
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                Standalone executable
              </li>
              <li className="flex items-center gap-2 text-dark-300">
                <CheckCircle className="w-4 h-4 text-accent-green" />
                No installation required
              </li>
            </ul>

            <a
              href={getDownloadUrl('windows')}
              className="flex items-center justify-center gap-2 w-full py-4 bg-accent-blue hover:bg-accent-blue/90 text-white font-semibold rounded-xl transition-colors"
            >
              <Download className="w-5 h-5" />
              Download for Windows
            </a>
            <p className="text-center text-dark-500 text-sm mt-3">
              Version {release?.tag_name?.replace('v', '') || LATEST_VERSION} • EXE installer
            </p>
          </div>
        </div>

        {/* GitHub Link */}
        <div className="text-center mt-12">
          <a
            href={`https://github.com/${GITHUB_REPO}/releases`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-dark-400 hover:text-accent-blue transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View all releases on GitHub
          </a>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-6xl mx-auto px-4 py-20 border-t border-dark-800">
        <h2 className="text-3xl font-bold text-center text-white mb-12">
          What's Included
        </h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-dark-800/30 rounded-xl p-6 border border-dark-700">
            <div className="w-12 h-12 bg-accent-blue/20 rounded-xl flex items-center justify-center mb-4">
              <span className="text-2xl">🎤</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Real-time Transcription</h3>
            <p className="text-dark-400">
              Instantly transcribe interview questions using your microphone or system audio.
            </p>
          </div>
          
          <div className="bg-dark-800/30 rounded-xl p-6 border border-dark-700">
            <div className="w-12 h-12 bg-accent-green/20 rounded-xl flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">AI-Powered Answers</h3>
            <p className="text-dark-400">
              Get intelligent, contextual responses based on your resume and job description.
            </p>
          </div>
          
          <div className="bg-dark-800/30 rounded-xl p-6 border border-dark-700">
            <div className="w-12 h-12 bg-accent-purple/20 rounded-xl flex items-center justify-center mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Global Hotkeys</h3>
            <p className="text-dark-400">
              Control recording and navigation with keyboard shortcuts that work anywhere.
            </p>
          </div>
        </div>
      </div>

      {/* Installation Instructions */}
      <div className="max-w-4xl mx-auto px-4 py-20 border-t border-dark-800">
        <h2 className="text-3xl font-bold text-center text-white mb-12">
          Installation Guide
        </h2>
        
        <div className="grid md:grid-cols-2 gap-12">
          <div>
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Apple className="w-5 h-5" /> macOS
            </h3>
            <ol className="space-y-3 text-dark-300">
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">1</span>
                Download the .dmg file
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">2</span>
                Open the DMG and drag to Applications
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">3</span>
                Right-click and select "Open" (first time only)
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">4</span>
                Grant Accessibility & Microphone permissions
              </li>
            </ol>
          </div>
          
          <div>
            <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <MonitorPlay className="w-5 h-5" /> Windows
            </h3>
            <ol className="space-y-3 text-dark-300">
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">1</span>
                Download the .exe file
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">2</span>
                Run the executable
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">3</span>
                Allow through Windows Firewall if prompted
              </li>
              <li className="flex gap-3">
                <span className="w-6 h-6 bg-dark-700 rounded-full flex items-center justify-center text-sm font-medium">4</span>
                Grant microphone permissions
              </li>
            </ol>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-dark-800 py-8">
        <div className="max-w-6xl mx-auto px-4 text-center text-dark-500">
          <p>© 2024 TechYera. All rights reserved.</p>
          <p className="mt-2">
            <a href="https://techyera.co" className="hover:text-accent-blue transition-colors">
              techyera.co
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}

