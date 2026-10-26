import React from 'react';
import { GQTEmblem } from './GQTEmblem';

interface GQTLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const GQTLogo: React.FC<GQTLogoProps> = ({
  className = '',
  size = 'md',
  showSubtitle = true,
}) => {
  const sizeMap = {
    sm: { emblemSize: 32, titleClass: 'text-sm', subClass: 'text-[9px]' },
    md: { emblemSize: 42, titleClass: 'text-base', subClass: 'text-[10px]' },
    lg: { emblemSize: 52, titleClass: 'text-xl', subClass: 'text-xs' },
  };

  const dim = sizeMap[size];

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
