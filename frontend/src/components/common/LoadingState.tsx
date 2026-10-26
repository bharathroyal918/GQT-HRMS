import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading platform data...',
  className,
}) => {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center space-y-3 min-h-[220px]',
        className
      )}
    >
      <Loader2 className="w-8 h-8 animate-spin text-gqt-blue" />
      <p className="text-sm font-medium text-gqt-neutral-600">{message}</p>
    </div>
  );
};
