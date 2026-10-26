import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GQTLogo } from '@/components/brand/GQTLogo';

describe('GQTLogo Component', () => {
  it('renders official Global Quest Technologies text', () => {
    render(<GQTLogo />);
    expect(screen.getByText('GLOBAL QUEST')).toBeInTheDocument();
    expect(screen.getByText('HRMS')).toBeInTheDocument();
    expect(screen.getByText(/Recruitment CRM/i)).toBeInTheDocument();
  });

  it('renders official SVG emblem', () => {
    render(<GQTLogo />);
    const emblem = screen.getByLabelText(/Global Quest Technologies Emblem/i);
    expect(emblem).toBeInTheDocument();
  });
});
