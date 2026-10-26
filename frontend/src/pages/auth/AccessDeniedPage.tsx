import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GQTLogo } from '../../components/brand/GQTLogo';
import { Button } from '../../components/common/Button';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const AccessDeniedPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gqt-neutral-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <GQTLogo variant="official" size="md" />
        </div>
      </div>

      <div className="mt-4 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm rounded-xl border border-gqt-neutral-200 text-center">
          <div className="mx-auto flex items-center justify-center h-14 w-14 rounded-full bg-amber-100 mb-5">
            <ShieldAlert className="h-8 w-8 text-amber-600" />
          </div>

          <h1 className="text-xl font-bold text-gqt-navy">403 — Access Denied</h1>
          <p className="mt-2 text-sm text-gqt-neutral-600 leading-relaxed">
            Your authenticated account does not possess the operational role privileges required to access this resource.
          </p>

          {user && (
            <div className="mt-4 p-3 bg-gqt-neutral-50 rounded-lg text-xs text-gqt-neutral-600 border border-gqt-neutral-200 text-left">
              <p><span className="font-semibold text-gqt-charcoal">Account:</span> {user.email}</p>
              <p className="mt-1">
                <span className="font-semibold text-gqt-charcoal">Active Roles:</span>{' '}
                {user.roles.length > 0 ? user.roles.join(', ') : 'No operational roles assigned'}
              </p>
            </div>
          )}

          <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/" className="w-full sm:w-auto">
              <Button variant="primary" className="w-full justify-center">
                <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
