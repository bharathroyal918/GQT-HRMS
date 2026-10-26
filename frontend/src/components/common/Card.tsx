import React, { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevation?: 'flat' | 'sm' | 'md';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, elevation = 'sm', children, ...props }, ref) => {
    const elevations = {
      flat: 'border border-gqt-neutral-200 bg-white',
      sm: 'border border-gqt-neutral-200/80 bg-white shadow-sm',
      md: 'border border-gqt-neutral-200/80 bg-white shadow-md',
    };

    return (
      <div
        ref={ref}
        className={cn('rounded-xl overflow-hidden', elevations[elevation], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn('p-5 border-b border-gqt-neutral-100', className)} {...props}>
      {children}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, children, ...props }, ref) => (
    <h3 ref={ref} className={cn('text-lg font-bold text-gqt-navy tracking-tight', className)} {...props}>
      {children}
    </h3>
  )
);
CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, children, ...props }, ref) => (
    <p ref={ref} className={cn('text-sm text-gqt-neutral-500 mt-0.5', className)} {...props}>
      {children}
    </p>
  )
);
CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn('p-5', className)} {...props}>
      {children}
    </div>
  )
);
CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn('p-4 bg-gqt-neutral-50/80 border-t border-gqt-neutral-100 flex items-center justify-between', className)} {...props}>
      {children}
    </div>
  )
);
CardFooter.displayName = 'CardFooter';
