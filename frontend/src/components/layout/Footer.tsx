import React from 'react';
import { ShieldCheck, Database, Layers } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-auto border-t border-gqt-neutral-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-gqt-neutral-500">
          <div className="flex items-center gap-2">
            <span className="font-bold text-gqt-navy">GLOBAL QUEST TECHNOLOGIES</span>
            <span>•</span>
            <span>GQT HRMS &amp; Recruitment CRM Platform</span>
            <span>•</span>
            <span>Version 1.0.0</span>
          </div>

          <div className="flex items-center gap-6 font-medium">
            <span className="flex items-center gap-1.5 text-emerald-700">
              <ShieldCheck className="w-4 h-4" />
              Fail-Closed Security
            </span>
            <span className="flex items-center gap-1.5 text-gqt-blue">
              <Database className="w-4 h-4" />
              PostgreSQL 16 Engine
            </span>
            <span className="flex items-center gap-1.5 text-gqt-charcoal">
              <Layers className="w-4 h-4" />
              13 Phases / 41 Steps
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
