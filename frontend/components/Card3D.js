import React, { useState, useRef } from 'react';

/**
 * 3D Animated Card Component
 * With depth, shadows, and hover effects
 */
export default function Card3D({
  children,
  className = '',
  variant = 'default',
  glowing = false,
  glowColor = '#00f2ff',
  interactive = false,
  onClick = null,
}) {
  const [isHovered, setIsHovered] = useState(false);
  const cardRef = useRef(null);

  const variants = {
    default: 'border-slate-700 bg-slate-900/60',
    primary: 'border-cyan-600/50 bg-cyan-950/30',
    success: 'border-green-600/50 bg-green-950/30',
    warning: 'border-yellow-600/50 bg-yellow-950/30',
    danger: 'border-red-600/50 bg-red-950/30',
    purple: 'border-purple-600/50 bg-purple-950/30',
  };

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`
        relative rounded-xl border-2 p-6 transition-all duration-300
        ${variants[variant]}
        ${interactive ? 'cursor-pointer' : ''}
        ${isHovered && interactive ? 'border-opacity-100 scale-105 shadow-2xl' : 'scale-100'}
        ${glowing ? 'shadow-lg' : ''}
        ${className}
      `}
      style={
        glowing && isHovered
          ? {
              boxShadow: `0 0 30px ${glowColor}40, inset 0 0 20px ${glowColor}20`,
            }
          : {}
      }
    >
      {/* Inner glow gradient */}
      <div
        className={`absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300 pointer-events-none ${
          isHovered ? 'opacity-20' : ''
        }`}
        style={{
          background: `radial-gradient(ellipse at center, ${glowColor}40, transparent)`,
        }}
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>

      {/* Border glow effect */}
      {glowing && isHovered && (
        <div
          className="absolute inset-0 rounded-xl border-2 animate-pulse pointer-events-none"
          style={{
            borderColor: glowColor,
            opacity: 0.5,
          }}
        />
      )}
    </div>
  );
}
