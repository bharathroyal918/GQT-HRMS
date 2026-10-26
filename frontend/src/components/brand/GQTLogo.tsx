import React from 'react';
import { GQTEmblem } from './GQTEmblem';

export interface GQTLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  variant?: 'horizontal' | 'stacked' | 'official';
}

export const GQTLogo: React.FC<GQTLogoProps> = ({
  className = '',
  size = 'md',
  showSubtitle = true,
  variant = 'horizontal',
}) => {
  const sizeMap = {
    sm: { emblemSize: 28, titleClass: 'text-sm', subClass: 'text-[9px]', officialH: 'h-10' },
    md: { emblemSize: 38, titleClass: 'text-base', subClass: 'text-[10px]', officialH: 'h-14' },
    lg: { emblemSize: 50, titleClass: 'text-xl', subClass: 'text-xs', officialH: 'h-20' },
  };

  const dim = sizeMap[size];

  if (variant === 'official') {
    return (
      <div className={`inline-flex flex-col items-center select-none ${className}`}>
        <img
          src="/images/brand/gqt-logo-tight.png"
          alt="Global Quest Technologies"
          aria-label="Global Quest Technologies Emblem"
          className={`object-contain max-w-full ${dim.officialH}`}
        />
        <div className="flex items-center gap-1.5 mt-1.5">
          <span className="font-bold tracking-wider text-gqt-navy text-xs uppercase">
            GLOBAL QUEST
          </span>
          <span className="font-extrabold tracking-normal text-gqt-blue text-xs uppercase bg-gqt-blue-light px-1.5 py-0.5 rounded">
            HRMS
          </span>
        </div>
        {showSubtitle && (
          <span className={`font-semibold tracking-wider uppercase text-gqt-neutral-500 mt-1 ${dim.subClass}`}>
            Recruitment CRM &amp; Talent Platform
          </span>
        )}
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      <GQTEmblem size={dim.emblemSize} />
      <div className="flex flex-col justify-center">
        <div className="flex items-baseline gap-1.5 leading-none">
          <span className={`font-black tracking-tight text-gqt-navy ${dim.titleClass}`}>
            GLOBAL QUEST
          </span>
          <span className="font-bold tracking-normal text-gqt-blue text-xs uppercase">
            HRMS
          </span>
        </div>
        {showSubtitle && (
          <span className={`font-semibold tracking-wider uppercase text-gqt-neutral-500 mt-1 ${dim.subClass}`}>
            Recruitment CRM &amp; Talent Platform
          </span>
        )}
      </div>
    </div>
  );
};

