import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '@/components/common/StatusBadge';

describe('StatusBadge Component', () => {
  it('renders label accurately', () => {
    render(<StatusBadge label="Operation Active" variant="success" />);
    expect(screen.getByText('Operation Active')).toBeInTheDocument();
  });

  it('applies variant styling for warning', () => {
    const { container } = render(<StatusBadge label="Pending Review" variant="warning" />);
    const badge = container.querySelector('span');
    expect(badge).toHaveClass('bg-amber-50');
    expect(badge).toHaveClass('text-amber-700');
  });

  it('hides dot indicator when showDot is false', () => {
    const { container } = render(<StatusBadge label="No Dot" showDot={false} />);
    const dots = container.querySelectorAll('span.rounded-full');
    // only the badge itself has rounded-full, no inner dot
    expect(dots.length).toBe(1);
  });
});
