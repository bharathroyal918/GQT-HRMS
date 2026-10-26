import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/lib/utils';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load content',
  message = 'An unexpected network error occurred while communicating with the GQT HRMS server.',
  onRetry,
  className,
}) => {
  return (
    <div
      role="alert"
      className={cn(
        'p-6 rounded-xl border border-rose-200 bg-rose-50/70 text-rose-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4',
        className
      )}
    >
      <div className="flex items-start gap-3.5">
        <AlertCircle className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-bold text-rose-950">{title}</h4>
          <p className="text-xs text-rose-800 mt-1 leading-relaxed max-w-xl">{message}</p>
        </div>
      </div>
      {onRetry && (
        <Button
          size="sm"
          variant="outline"
          onClick={onRetry}
          className="border-rose-300 bg-white text-rose-900 hover:bg-rose-100/50 shrink-0 self-end sm:self-center"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" />
          Retry
        </Button>
      )}
    </div>
  );
};
