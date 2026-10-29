import React, { Suspense } from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import { RouteLoadingFallback } from './RouteLoadingFallback';
import { RouteErrorBoundary } from '../common/RouteErrorBoundary';

export const AppShell: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gqt-neutral-50 text-gqt-charcoal selection:bg-gqt-blue-light selection:text-gqt-blue">
      <Navbar />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <RouteErrorBoundary>
          <Suspense fallback={<RouteLoadingFallback />}>
            <Outlet />
          </Suspense>
        </RouteErrorBoundary>
      </main>
      <Footer />
    </div>
  );
};
