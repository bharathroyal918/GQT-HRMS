import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { GQTLogo } from '../brand/GQTLogo';
import { StatusBadge } from '../common/StatusBadge';
import { LayoutDashboard, Activity, FileCode2 } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const navLinks = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'System Diagnostics', href: '/diagnostics', icon: Activity },
  ];

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-gqt-neutral-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <Link to="/" className="transition-transform hover:scale-[1.01]">
            <GQTLogo size="sm" />
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-gqt-blue-light text-gqt-blue'
                      : 'text-gqt-neutral-600 hover:text-gqt-navy hover:bg-gqt-neutral-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Tools & Badges */}
          <div className="flex items-center gap-3">
            <StatusBadge variant="info" label="Foundation Stage" />
            <a
              href="http://localhost:8000/api/v1/schema/swagger/"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-gqt-neutral-300 text-gqt-charcoal hover:bg-gqt-neutral-100 transition-colors"
            >
              <FileCode2 className="w-3.5 h-3.5 text-gqt-blue" />
              API Docs
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
