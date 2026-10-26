import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Upload,
  CheckCircle,
  AlertTriangle,
  Download,
  Edit2,
  Save,
  X,
} from 'lucide-react';
import { studentsApi } from '@/api/studentsApi';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const StudentProfileWorkspacePage: React.FC = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isEditing, setIsEditing] = useState(false);
  const [editCgpa, setEditCgpa] = useState('');
  const [editDept, setEditDept] = useState('');
  const [editYear, setEditYear] = useState<number>(2025);
  const [editBacklogs, setEditBacklogs] = useState<number>(0);
  const [editPhone, setEditPhone] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Fetch current student profile
  const {
    data: profile,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['student-profile-me'],
    queryFn: () => studentsApi.getProfileMe(),
  });

  // Profile update mutation
  const updateMutation = useMutation({
    mutationFn: () =>
      studentsApi.updateProfileMe({
        cgpa: editCgpa,
        department: editDept,
        graduation_year: editYear,
        active_backlogs: editBacklogs,
        phone_number: editPhone,
      }),
    onSuccess: () => {
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['student-profile-me'] });
    },
  });

  // Resume upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => studentsApi.uploadResume(file),
    onSuccess: (res) => {
      setUploadSuccess(`Resume revision v${res.version_number} uploaded successfully.`);
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['student-profile-me'] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Resume upload failed.';
      setUploadError(msg);
      setUploadSuccess(null);
    },
  });

  const handleStartEdit = () => {
    if (profile) {
      setEditCgpa(String(profile.cgpa));
      setEditDept(profile.department);
      setEditYear(profile.graduation_year);
      setEditBacklogs(profile.active_backlogs);
      setEditPhone(profile.phone_number);
      setIsEditing(true);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploadSuccess(null);

    // Client-side pre-flight size check (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setUploadError('File exceeds 5MB size limit.');
      return;
    }

    // Client-side magic bytes pre-check (%PDF-)
    try {
      const buffer = await file.slice(0, 5).arrayBuffer();
      const header = new TextDecoder().decode(buffer);
      if (!header.startsWith('%PDF-')) {
        setUploadError('Invalid document format. Only valid PDF files with %PDF- header are accepted.');
        return;
      }
    } catch {
      // Fallback to server check
    }

    uploadMutation.mutate(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  if (isLoading) return <LoadingState message="Loading your student profile..." />;
  if (error || !profile) return <ErrorState message="Could not load your student profile." />;

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
            Step 12: Profile & Documents
          </span>
          <h1 className="text-2xl font-bold text-gqt-navy mt-1">{profile.full_name}</h1>
          <p className="text-sm text-gqt-neutral-500">
            Roll No: <span className="font-semibold text-gqt-navy">{profile.roll_number}</span> &bull;{' '}
            {profile.institutional_email}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {profile.is_verified_by_placement ? (
            <StatusBadge variant="success" label="Placement Verified" />
          ) : (
            <StatusBadge variant="warning" label="Verification Pending" />
          )}
        </div>
      </div>

      {/* Profile Overview & Edit Form */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base">Academic Records & Credentials</CardTitle>
            <CardDescription>
              Verified metrics utilized by the Step 13 Eligibility Verification Engine.
            </CardDescription>
          </div>
          {!isEditing ? (
            <Button variant="outline" size="sm" onClick={handleStartEdit}>
              <Edit2 className="w-3.5 h-3.5 mr-1.5" />
              Edit Academic Info
            </Button>
          ) : (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsEditing(false)}
                disabled={updateMutation.isPending}
              >
                <X className="w-3.5 h-3.5 mr-1" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
              >
                <Save className="w-3.5 h-3.5 mr-1" />
                {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {!isEditing ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div className="p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-100">
                <span className="text-xs text-gqt-neutral-400 font-medium uppercase tracking-wider block">
                  Degree & Program
                </span>
                <span className="font-semibold text-gqt-navy mt-0.5 block">{profile.degree}</span>
                <span className="text-xs text-gqt-neutral-500">{profile.department}</span>
              </div>
              <div className="p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-100">
                <span className="text-xs text-gqt-neutral-400 font-medium uppercase tracking-wider block">
                  Academic CGPA
                </span>
                <span className="text-xl font-bold text-gqt-navy mt-0.5 block">{profile.cgpa}</span>
                <span className="text-xs text-gqt-neutral-500">10.0 scale</span>
              </div>
              <div className="p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-100">
                <span className="text-xs text-gqt-neutral-400 font-medium uppercase tracking-wider block">
                  Active Backlogs
                </span>
                <span
                  className={`text-xl font-bold mt-0.5 block ${
                    profile.active_backlogs > 0 ? 'text-amber-600' : 'text-emerald-600'
                  }`}
                >
                  {profile.active_backlogs}
                </span>
                <span className="text-xs text-gqt-neutral-500">Uncleared arrears</span>
              </div>
              <div className="p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-100">
                <span className="text-xs text-gqt-neutral-400 font-medium uppercase tracking-wider block">
                  Passing Batch
                </span>
                <span className="text-xl font-bold text-gqt-navy mt-0.5 block">{profile.graduation_year}</span>
                <span className="text-xs text-gqt-neutral-500">Graduation Year</span>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Department
                </label>
                <input
                  type="text"
                  value={editDept}
                  onChange={e => setEditDept(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  CGPA (10.0 scale)
                </label>
                <input
                  type="text"
                  value={editCgpa}
                  onChange={e => setEditCgpa(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Active Backlogs
                </label>
                <input
                  type="number"
                  value={editBacklogs}
                  onChange={e => setEditBacklogs(parseInt(e.target.value) || 0)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Graduation Year
                </label>
                <input
                  type="number"
                  value={editYear}
                  onChange={e => setEditYear(parseInt(e.target.value) || 2025)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Phone Number
                </label>
                <input
                  type="text"
                  value={editPhone}
                  onChange={e => setEditPhone(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resume Upload & Document Vault */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <FileText className="w-5 h-5 text-gqt-blue" />
            Resume Document Vault
          </CardTitle>
          <CardDescription>
            Ingest candidate resumes with binary magic bytes validation (%PDF-), SHA-256 fingerprinting, and monotonic versioning.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {uploadError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}
          {uploadSuccess && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{uploadSuccess}</span>
            </div>
          )}

          {/* Upload Drop Zone */}
          <div className="border-2 border-dashed border-gqt-neutral-200 rounded-xl p-8 text-center hover:border-gqt-blue/60 transition-colors bg-gqt-neutral-50/50">
            <div className="w-12 h-12 bg-blue-50 text-gqt-blue rounded-full flex items-center justify-center mx-auto mb-3">
              <Upload className="w-6 h-6" />
            </div>
            <h4 className="font-semibold text-sm text-gqt-navy mb-1">
              Upload Updated Placement Resume
            </h4>
            <p className="text-xs text-gqt-neutral-500 mb-4 max-w-sm mx-auto">
              Only standard PDF files (%PDF-) up to 5MB in size are permitted. Uploading automatically archives previous revisions and increments version number.
            </p>
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
            >
              <Upload className="w-4 h-4 mr-1.5" />
              {uploadMutation.isPending ? 'Validating & Uploading...' : 'Select PDF File'}
            </Button>
          </div>

          {/* Version History Table */}
          <div>
            <h4 className="text-sm font-semibold text-gqt-navy mb-3">
              Uploaded Resume Revision History
            </h4>
            {!profile.resumes || profile.resumes.length === 0 ? (
              <p className="text-sm text-gqt-neutral-500 py-4 text-center border rounded-lg">
                No resume has been uploaded yet. Please upload a PDF to apply for placement opportunities.
              </p>
            ) : (
              <div className="overflow-x-auto border border-gqt-neutral-200 rounded-lg">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="bg-gqt-neutral-50 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider border-b border-gqt-neutral-200">
                      <th className="py-2.5 px-3">Version</th>
                      <th className="py-2.5 px-3">Filename</th>
                      <th className="py-2.5 px-3">Size</th>
                      <th className="py-2.5 px-3">SHA-256 Digest</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Uploaded</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gqt-neutral-100">
                    {profile.resumes.map(r => (
                      <tr key={r.id} className="hover:bg-gqt-neutral-50/50">
                        <td className="py-3 px-3 font-semibold text-gqt-navy">
                          v{r.version_number}
                        </td>
                        <td className="py-3 px-3 text-gqt-neutral-700">{r.file_name}</td>
                        <td className="py-3 px-3 text-xs text-gqt-neutral-500">
                          {(r.file_size_bytes / 1024).toFixed(1)} KB
                        </td>
                        <td className="py-3 px-3 font-mono text-xs text-gqt-neutral-400">
                          {r.sha256_hash.substring(0, 12)}...
                        </td>
                        <td className="py-3 px-3">
                          {r.is_current ? (
                            <StatusBadge variant="success" label="Active / Current" />
                          ) : (
                            <span className="text-xs text-gqt-neutral-400 font-medium">Archived</span>
                          )}
                        </td>
                        <td className="py-3 px-3 text-xs text-gqt-neutral-500">
                          {new Date(r.uploaded_at).toLocaleDateString()}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <a
                            href={studentsApi.getResumeDownloadUrl(r.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <Button variant="outline" size="sm">
                              <Download className="w-3.5 h-3.5 mr-1" />
                              Download
                            </Button>
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
