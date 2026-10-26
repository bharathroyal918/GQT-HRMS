import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/common/Button';
import { AlertTriangle, Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 space-y-4">
      <div className="w-16 h-16 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center">
        <AlertTriangle className="w-8 h-8" />
      </div>
      <h2 className="text-2xl font-black text-gqt-navy">404 - Page Not Found</h2>
      <p className="text-sm text-gqt-neutral-500 max-w-md">
        The requested module or resource does not exist in the GQT HRMS platform.
      </p>
      <Link to="/" className="pt-2">
        <Button variant="primary" size="md">
          <Home className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Button>
      </Link>
    </div>
  );
};
