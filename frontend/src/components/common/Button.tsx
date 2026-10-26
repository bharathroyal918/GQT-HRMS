import React, { ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none';

    const variants = {
      primary:
        'bg-gqt-navy hover:bg-gqt-navy-light text-white focus:ring-gqt-blue shadow-sm',
      secondary:
        'bg-gqt-blue hover:bg-gqt-blue-vivid text-white focus:ring-gqt-blue shadow-sm',
      outline:
        'border border-gqt-neutral-300 bg-white text-gqt-charcoal hover:bg-gqt-neutral-100 focus:ring-gqt-blue',
      danger:
        'bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500 shadow-sm',
      ghost:
        'text-gqt-charcoal hover:bg-gqt-neutral-100 focus:ring-gqt-blue',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-xs gap-1.5',
      md: 'px-4 py-2 text-sm gap-2',
      lg: 'px-5 py-2.5 text-base gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-current shrink-0" />
        ) : (
          leftIcon && <span className="shrink-0">{leftIcon}</span>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
