import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GQTLogo } from '../brand/GQTLogo';
import {
  LayoutDashboard,
  Activity,
  FileCode2,
  LogOut,
  User as UserIcon,
  Building2,
  Users,
  PhoneCall,
  Calendar,
  Briefcase,
  FileCheck,
  Palette,
  Sparkles,
  GraduationCap,
  ShieldCheck,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user, isAuthenticated, logout, hasAnyRole, hasRole } = useAuth();

  const canAccessCRM = hasAnyRole([
    'ADMIN',
    'PLACEMENT_HEAD',
    'PLACEMENT_OFFICER',
    'HR_RELATIONSHIP_MGR',
    'AUDITOR',
  ]);

  const canAccessJobs = hasAnyRole([
    'ADMIN',
    'PLACEMENT_HEAD',
    'PLACEMENT_OFFICER',
    'HR_RELATIONSHIP_MGR',
    'CREATIVE_DESIGNER',
    'AUDITOR',
  ]);

  const canAccessCreatives = hasAnyRole([
    'ADMIN',
    'PLACEMENT_HEAD',
    'PLACEMENT_OFFICER',
    'CREATIVE_DESIGNER',
    'AUDITOR',
  ]);

  const navLinks = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    ...(canAccessCRM
      ? [
          { name: 'Corporate CRM', href: '/crm', icon: Building2 },
          { name: 'Companies', href: '/crm/companies', icon: Building2 },
          { name: 'Contacts', href: '/crm/contacts', icon: Users },
          { name: 'Outreach', href: '/crm/outreach', icon: PhoneCall },
          { name: 'Follow-ups', href: '/crm/follow-ups', icon: Calendar },
        ]
      : []),
    ...(canAccessJobs
      ? [
          { name: 'Job Requirements', href: '/jobs', icon: Briefcase },
          { name: 'Review & Approvals', href: '/jobs/approvals', icon: FileCheck },
        ]
      : []),
    ...(canAccessCreatives
      ? [
          { name: 'Creative Studio', href: '/creatives', icon: Palette },
          ...(hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'])
            ? [{ name: 'Creative Reviews', href: '/creatives/queue', icon: Sparkles }]
            : []),
          ...(hasRole('CREATIVE_DESIGNER')
            ? [{ name: 'My Tasks', href: '/creatives/my-tasks', icon: Sparkles }]
            : []),
        ]
      : []),
    ...(hasRole('STUDENT') ? [{ name: 'My Profile & Resume', href: '/students/profile', icon: GraduationCap }] : []),
    ...(hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR'])
      ? [{ name: 'Student Directory', href: '/students', icon: GraduationCap }]
      : []),
    { name: 'Resume Reviews', href: '/preparation/resume-reviews', icon: FileCheck },
    { name: 'Assessments', href: '/preparation/assessments', icon: Sparkles },
    { name: 'Mock Interviews', href: '/preparation/mock-interviews', icon: Users },
    ...(hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR'])
      ? [{ name: 'Readiness Gate', href: '/preparation/readiness-gate', icon: ShieldCheck }]
      : []),
    ...(hasRole('ADMIN') ? [{ name: 'Diagnostics', href: '/diagnostics', icon: Activity }] : []),
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

          {/* Right Tools, User State & Actions */}
          <div className="flex items-center gap-3">
            <a
              href="http://localhost:8000/api/v1/schema/swagger/"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border border-gqt-neutral-300 text-gqt-charcoal hover:bg-gqt-neutral-100 transition-colors"
            >
              <FileCode2 className="w-3.5 h-3.5 text-gqt-blue" />
              API Docs
            </a>

            {isAuthenticated && user ? (
              <div className="flex items-center gap-2.5 pl-2 border-l border-gqt-neutral-200">
                <div className="hidden sm:flex flex-col items-end leading-none">
                  <span className="text-xs font-bold text-gqt-navy">{user.full_name}</span>
                  <span className="text-[10px] font-semibold text-gqt-neutral-500 uppercase mt-0.5">
                    {user.roles.length > 0 ? user.roles[0] : 'Member'}
                  </span>
                </div>
                <button
                  onClick={() => logout()}
                  title="Sign out of GQT HRMS"
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-red-600 hover:bg-red-50 transition-colors border border-transparent hover:border-red-200"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-gqt-blue text-white hover:bg-gqt-blue-dark transition-colors shadow-sm"
              >
                <UserIcon className="w-3.5 h-3.5" />
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
