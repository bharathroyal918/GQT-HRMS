import React from 'react';

interface GQTEmblemProps {
  className?: string;
  size?: number;
}

export const GQTEmblem: React.FC<GQTEmblemProps> = ({ className = '', size = 40 }) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      aria-label="Global Quest Technologies Emblem"
    >
      <defs>
        <linearGradient id="gqtBlueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#001B4D" />
          <stop offset="100%" stopColor="#005BBB" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="100" height="100" rx="22" fill="url(#gqtBlueGrad)" />
      <circle cx="50" cy="50" r="32" fill="none" stroke="#FFFFFF" strokeWidth="4" strokeOpacity="0.35" />
      <circle cx="50" cy="50" r="22" fill="none" stroke="#FFFFFF" strokeWidth="3" />
      <path d="M50 24 L50 76 M24 50 L76 50" stroke="#00D2FF" strokeWidth="3" strokeLinecap="round" />
      <circle cx="50" cy="50" r="9" fill="#FFFFFF" />
    </svg>
  );
};
