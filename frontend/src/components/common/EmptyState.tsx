import React, { ReactNode } from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon,
  action,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center rounded-xl border-2 border-dashed border-gqt-neutral-200 bg-white min-h-[260px]',
        className
      )}
    >
      <div className="w-12 h-12 rounded-full bg-gqt-neutral-100 flex items-center justify-center text-gqt-neutral-500 mb-4">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <h4 className="text-base font-bold text-gqt-charcoal mb-1">{title}</h4>
      {description && (
        <p className="text-sm text-gqt-neutral-500 max-w-sm mb-6 leading-relaxed">
          {description}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
};
