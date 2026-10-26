import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { studentsApi } from '@/api/studentsApi';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Input } from '@/components/common/Input';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const StudentDirectoryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedYear, setSelectedYear] = useState('');

  const {
    data: profiles,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['student-profiles', searchTerm, selectedDept, selectedYear],
    queryFn: () =>
      studentsApi.listProfiles({
        search: searchTerm || undefined,
        department: selectedDept || undefined,
        graduation_year: selectedYear || undefined,
      }),
  });

  if (isLoading) return <LoadingState message="Loading registered students..." />;
  if (error) return <ErrorState message="Could not load student directory." />;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
            Step 11 & 12 Directory
          </span>
          <h1 className="text-2xl font-bold text-gqt-navy mt-1">Student Talent Directory</h1>
          <p className="text-sm text-gqt-neutral-500">
            Enrolled student profiles and uploaded placement resume documents.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              placeholder="Search by name, roll no, email..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <select
              value={selectedDept}
              onChange={e => setSelectedDept(e.target.value)}
              className="rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">All Departments</option>
              <option value="Computer Science">Computer Science & Engineering</option>
              <option value="Information Science">Information Science & Engineering</option>
              <option value="Electronics">Electronics & Communication</option>
              <option value="Mechanical">Mechanical Engineering</option>
            </select>
            <select
              value={selectedYear}
              onChange={e => setSelectedYear(e.target.value)}
              className="rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">All Passing Batches</option>
              <option value="2024">2024</option>
              <option value="2025">2025</option>
              <option value="2026">2026</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Profiles Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Registered Students ({profiles?.length || 0})</CardTitle>
          <CardDescription>
            All registered candidates available for eligibility verification and campus hiring drives.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!profiles || profiles.length === 0 ? (
            <p className="text-sm text-gqt-neutral-500 py-8 text-center">
              No students found matching your search criteria.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gqt-neutral-200 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <th className="pb-3">Roll Number</th>
                    <th className="pb-3">Candidate</th>
                    <th className="pb-3">Discipline</th>
                    <th className="pb-3">CGPA</th>
                    <th className="pb-3">Batch</th>
                    <th className="pb-3">Active Resume</th>
                    <th className="pb-3">Placement Verification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {profiles.map(p => (
                    <tr key={p.id} className="hover:bg-gqt-neutral-50/50">
                      <td className="py-3 font-mono font-bold text-xs text-gqt-navy">{p.roll_number}</td>
                      <td className="py-3">
                        <span className="font-semibold text-gqt-navy block">{p.full_name}</span>
                        <span className="text-xs text-gqt-neutral-400">{p.institutional_email}</span>
                      </td>
                      <td className="py-3 text-gqt-neutral-600">{p.department}</td>
                      <td className="py-3 font-semibold text-gqt-navy">{p.cgpa}</td>
                      <td className="py-3 text-gqt-neutral-500">{p.graduation_year}</td>
                      <td className="py-3">
                        {p.current_resume ? (
                          <a
                            href={studentsApi.getResumeDownloadUrl(p.current_resume.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-xs font-medium text-gqt-blue hover:underline"
                          >
                            <FileText className="w-3.5 h-3.5 mr-1" />
                            v{p.current_resume.version_number} (Active)
                          </a>
                        ) : (
                          <span className="text-xs text-amber-600 font-medium">Pending Upload</span>
                        )}
                      </td>
                      <td className="py-3">
                        {p.is_verified_by_placement ? (
                          <StatusBadge variant="success" label="Verified" />
                        ) : (
                          <StatusBadge variant="neutral" label="Unverified" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
