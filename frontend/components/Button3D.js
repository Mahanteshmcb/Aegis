import React, { useState, useRef } from 'react';

/**
 * 3D Animated Button with hover effects
 */
export default function Button3D({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  icon: Icon = null,
}) {
  const [isHovered, setIsHovered] = useState(false);
  const buttonRef = useRef(null);

  const baseStyles = 'relative font-bold uppercase tracking-wider transition-all duration-300 overflow-hidden';

  const variants = {
    primary:
      'bg-gradient-to-r from-cyan-600 to-blue-600 text-white hover:shadow-lg hover:shadow-cyan-500/50',
    secondary:
      'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:shadow-purple-500/50',
    success:
      'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:shadow-lg hover:shadow-green-500/50',
    danger: 'bg-gradient-to-r from-red-600 to-orange-600 text-white hover:shadow-lg hover:shadow-red-500/50',
    ghost:
      'border-2 border-cyan-500/50 text-cyan-300 hover:border-cyan-300 hover:bg-cyan-500/10 hover:shadow-lg hover:shadow-cyan-500/30',
  };

  const sizes = {
    sm: 'px-3 py-1 text-xs',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  return (
    <button
      ref={buttonRef}
      onClick={onClick}
      disabled={disabled}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className} ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } rounded-lg`}
    >
      {/* Shimmer effect */}
      <div
        className={`absolute inset-0 opacity-0 transition-opacity duration-300 ${
          isHovered ? 'opacity-100' : ''
        }`}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
      </div>

      {/* Glow effect */}
      <div
        className={`absolute inset-0 blur-xl opacity-0 transition-opacity duration-300 ${
          isHovered ? 'opacity-100' : ''
        }`}
        style={{ backgroundColor: 'currentColor', filter: 'blur(20px)' }}
      />

      {/* Content */}
      <div className="relative flex items-center justify-center gap-2">
        {Icon && <Icon size={20} />}
        {children}
      </div>

      {/* 3D depth effect border */}
      <div
        className={`absolute inset-0 border-2 border-white/20 rounded-lg transition-all duration-300 ${
          isHovered ? 'border-white/40 scale-105' : 'scale-100'
        }`}
        style={{ pointerEvents: 'none' }}
      />
    </button>
  );
}
