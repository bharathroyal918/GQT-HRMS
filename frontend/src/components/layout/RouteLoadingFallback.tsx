import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface RouteLoadingFallbackProps {
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

export const RouteLoadingFallback: React.FC<RouteLoadingFallbackProps> = ({
  message = 'Loading workspace...',
  fullScreen = false,
  className,
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading page"
      className={cn(
        'flex flex-col items-center justify-center text-center p-8 transition-opacity duration-200',
        fullScreen ? 'min-h-screen bg-gqt-neutral-50' : 'min-h-[400px] w-full',
        className
      )}
    >
      <div className="relative flex items-center justify-center">
        {/* Subtle branded pulsing glow */}
        <div className="absolute w-12 h-12 rounded-full bg-gqt-blue/10 animate-ping" />
        <Loader2 className="w-8 h-8 animate-spin text-gqt-blue relative z-10" />
      </div>
      <p className="mt-4 text-sm font-semibold text-gqt-navy-900 tracking-tight">
        {message}
      </p>
      <p className="mt-1 text-xs text-gqt-neutral-500">
        Connecting to GQT HRMS services
      </p>
    </div>
  );
};

