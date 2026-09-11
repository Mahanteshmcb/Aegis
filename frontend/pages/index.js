import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ChevronRight, Zap, Shield, BarChart3, Cpu } from 'lucide-react';
import dynamic from 'next/dynamic';
const Background3D = dynamic(() => import('../components/3d/Background3D'), { ssr: false });
import Button3D from '../components/Button3D';
import Card3D from '../components/Card3D';
import useCurrentUser from '../hooks/useCurrentUser';

export default function Home() {
  const router = useRouter();
  const { user, loading } = useCurrentUser();
  const [selectedFeature, setSelectedFeature] = useState(null);

  // Send visitors to authentication first; authenticated users go to the dashboard.
  useEffect(() => {
    if (!loading) {
      router.replace(user ? '/estate-dashboard' : '/login');
    }
  }, [user, loading, router]);

  if (loading || !router.isReady) {
    return <div className="min-h-screen bg-[#050816]" />;
  }

  if (!user) {
    return null;
  }

  const features = [
    {
      icon: Zap,
      title: 'Lightning Fast',
      description: 'Real-time estate management with instant updates across all systems.',
      color: '#FFD700',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Military-grade encryption and multi-layer authentication protocols.',
      color: '#00FF00',
    },
    {
      icon: BarChart3,
      title: 'Advanced Analytics',
      description: 'AI-powered insights and predictive analytics for your entire estate.',
      color: '#00BFFF',
    },
    {
      icon: Cpu,
      title: '3D Visualization',
      description: 'Immersive spatial management with interactive 3D environments.',
      color: '#FF1493',
    },
  ];

  return (
    <Background3D glowColor="#00f2ff">
      <div className="relative min-h-screen flex flex-col">
        {/* Navigation */}
        <nav className="relative z-50 flex items-center justify-between px-8 py-6 border-b border-slate-800/50 bg-gradient-to-r from-black/40 to-black/20">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center text-white font-bold">
              ⚔️
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              AEGIS
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-aegis-muted hover:text-white transition">
              Sign In
            </Link>
            <Link href="/signup" className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition">
              Get Started
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <div className="flex-1 flex items-center justify-center px-8 py-20">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            {/* Main Title */}
            <div className="space-y-4">
              <h1 className="text-7xl font-black bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-300 bg-clip-text text-transparent animate-pulse">
                ESTATE COMMAND CENTER
              </h1>
              <p className="text-2xl text-aegis-muted font-light">
                Advanced automation and monitoring for intelligent spaces
              </p>
            </div>

            {/* Subheading */}
            <div className="space-y-3">
              <p className="text-lg text-slate-300">
                🚀 Deploy autonomous robots • 📡 Monitor environmental sensors • 🎯 Manage security zones
              </p>
              <p className="text-sm text-slate-400 font-mono">
                Powered by AI, secured by encryption, visualized in 3D
              </p>
            </div>

            {/* CTA Buttons */}
            <div className="flex gap-4 justify-center pt-8 flex-wrap">
              <Link href="/login">
                <Button3D variant="primary" size="lg">
                  Enter Control Center
                  <ChevronRight size={20} />
                </Button3D>
              </Link>
              <Link href="/3d-scene">
                <Button3D variant="ghost" size="lg">
                  View 3D Demo
                </Button3D>
              </Link>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="relative z-10 px-8 py-20 bg-gradient-to-t from-black/60 to-transparent">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-4xl font-bold text-center text-cyan-300 mb-16 tracking-wider">
              CORE CAPABILITIES
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {features.map((feature, idx) => {
                const Icon = feature.icon;
                return (
                  <Card3D
                    key={idx}
                    variant={idx === 0 ? 'primary' : idx === 1 ? 'success' : idx === 2 ? 'warning' : 'danger'}
                    glowing
                    glowColor={feature.color}
                    interactive
                    onClick={() => setSelectedFeature(idx)}
                  >
                    <div className="space-y-4">
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: `${feature.color}20` }}
                      >
                        <Icon size={24} style={{ color: feature.color }} />
                      </div>
                      <h3 className="text-lg font-bold text-white">{feature.title}</h3>
                      <p className="text-sm text-slate-300">{feature.description}</p>
                    </div>
                  </Card3D>
                );
              })}
            </div>
          </div>
        </div>

        {/* Stats Section */}
        <div className="relative z-10 px-8 py-16">
          <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="space-y-2">
              <p className="text-4xl font-bold text-cyan-400">99.9%</p>
              <p className="text-sm text-aegis-muted">System Uptime</p>
            </div>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-green-400">10k+</p>
              <p className="text-sm text-aegis-muted">Active Devices</p>
            </div>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-purple-400">50ms</p>
              <p className="text-sm text-aegis-muted">Avg Latency</p>
            </div>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-pink-400">256-bit</p>
              <p className="text-sm text-aegis-muted">Encryption</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 px-8 py-8 border-t border-slate-800/50 bg-black/40 text-center">
          <p className="text-sm text-aegis-muted">
            © 2026 Aegis Estate Command Center. Advanced robotics and automation.
          </p>
        </div>
      </div>
    </Background3D>
  );
}
