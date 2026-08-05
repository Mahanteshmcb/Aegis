import React from 'react';

/**
 * 3D Page Layout Wrapper
 * Provides consistent 3D styling and background for all management pages
 */
export default function Layout3D({
  children,
  title,
  subtitle,
  icon = '📊',
  glowColor = '#00f2ff',
}) {
  return (
    <div className="relative min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black">
      {/* Animated background grid */}
      <div className="absolute inset-0 bg-grid-slate-800/[0.04] pointer-events-none" />

      {/* Gradient overlays */}
      <div className="absolute top-0 left-0 w-1/2 h-1/2 bg-gradient-radial from-cyan-600/20 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-gradient-radial from-purple-600/20 to-transparent blur-3xl pointer-events-none" />

      {/* Content */}
      <div className="relative z-10">
        {/* Header */}
        <div className="px-8 py-8 border-b border-slate-800/50 bg-gradient-to-r from-black/40 to-black/20 backdrop-blur-sm">
          <div className="flex items-center gap-4 mb-4">
            <div className="text-4xl">{icon}</div>
            <div>
              <h1 className="text-4xl font-bold text-aegis-primary tracking-[0.2em]">{title}</h1>
              {subtitle && <p className="text-sm text-aegis-muted mt-1">{subtitle}</p>}
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="px-8 py-12">{children}</div>
      </div>
    </div>
  );
}
