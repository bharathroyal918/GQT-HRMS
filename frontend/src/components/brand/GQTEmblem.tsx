import React from 'react';

interface GQTEmblemProps {
  className?: string;
  size?: number;
}

export const GQTEmblem: React.FC<GQTEmblemProps> = ({ className = '', size = 38 }) => {
  return (
    <img
      src="/images/brand/gqt-emblem.png"
      alt="Global Quest Technologies Emblem"
      aria-label="Global Quest Technologies Emblem"
      className={`inline-block object-contain select-none ${className}`}
      style={{ height: size, width: 'auto' }}
      loading="eager"
    />
  );
};

