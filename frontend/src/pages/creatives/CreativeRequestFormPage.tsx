import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Palette,
  ArrowLeft,
  Briefcase,
  AlertCircle,
  FileCheck,
  Check,
  Info,
} from 'lucide-react';
import { creativesApi } from '@/api/creativesApi';
import { jobsApi } from '@/api/jobsApi';
import { Button } from '@/components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import { JobRequirementListItem } from '@/types/jobs';

const creativeFormSchema = z.object({
  job_requirement_id: z.string().uuid({ message: 'Please select an approved Job Requirement' }),
  title: z.string().min(3, { message: 'Title must be at least 3 characters' }),
  deliverable_type: z.enum(['FLYER', 'BANNER', 'SOCIAL_POST', 'COMBINED_PACK']),
  priority: z.enum(['LOW', 'MEDIUM', 'HIGH', 'URGENT']),
  brief: z.string().min(10, { message: 'Creative brief must be at least 10 characters' }),
  target_audience: z.string().optional(),
  registration_link: z.string().url({ message: 'Must be a valid URL' }).or(z.literal('')),
  qr_code_target_url: z.string().url({ message: 'Must be a valid URL' }).or(z.literal('')),
  contact_email: z.string().email({ message: 'Must be a valid email' }).or(z.literal('')),
  contact_phone: z.string().optional(),
  production_deadline: z.string().optional(),
});

type CreativeFormValues = z.infer<typeof creativeFormSchema>;

export const CreativeRequestFormPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreativeFormValues>({
    resolver: zodResolver(creativeFormSchema),
    defaultValues: {
      deliverable_type: 'COMBINED_PACK',
      priority: 'MEDIUM',
      brief: '',
      target_audience: '',
      registration_link: '',
      qr_code_target_url: '',
      contact_email: '',
      contact_phone: '',
      production_deadline: '',
    },
  });

  const selectedJobId = watch('job_requirement_id');

  // Fetch approved job requirements only (Step 8 prerequisite)
  const { data: approvedJobsData, isLoading: isLoadingJobs } = useQuery({
    queryKey: ['approved-jobs-for-creatives'],
    queryFn: () => jobsApi.getJobs({ status: 'APPROVED' }),
  });

  const approvedJobs = approvedJobsData?.data || [];
  const selectedJob = approvedJobs.find((j: JobRequirementListItem) => j.id === selectedJobId);

  // Auto-fill brief template when an approved job is selected
  useEffect(() => {
    if (selectedJob) {
      setValue('title', `${selectedJob.company_name} — ${selectedJob.title} Creative Campaign`);
      const defaultBrief = (
        `Placement Drive Promotional Campaign for ${selectedJob.company_name}\n` +
        `Role: ${selectedJob.title}\n` +
        `Location: ${selectedJob.location}\n` +
        `Package: ${selectedJob.min_salary} - ${selectedJob.max_salary} LPA\n` +
        `Registration Deadline: ${new Date(selectedJob.registration_deadline).toLocaleDateString()}\n\n` +
        `Key Deliverables:\n` +
        `- Official employer branding logo.\n` +
        `- High-contrast scannable QR code linking to candidate portal registration.\n` +
        `- Institutional GQT placement contact details.`
      );
      setValue('brief', defaultBrief);
    }
  }, [selectedJob, setValue]);

  const createMutation = useMutation({
    mutationFn: (values: CreativeFormValues) => {
      const payload: Record<string, unknown> = {
        ...values,
        production_deadline: values.production_deadline ? new Date(values.production_deadline).toISOString() : null,
      };
      return creativesApi.createCreativeRequest(payload);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['creative-requests'] });
      queryClient.invalidateQueries({ queryKey: ['creative-metrics'] });
      navigate(`/creatives/${data.id}`);
    },
  });

  const onSubmit = (values: CreativeFormValues) => {
    createMutation.mutate(values);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Back Button & Title */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/creatives')}
          className="text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Directory
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Palette className="w-6 h-6 text-[#005BBB]" />
            Initiate Creative Request (Step 8)
          </h1>
          <p className="text-sm text-slate-600">
            Dispatch creative production briefs for approved job opportunities to Graphic Designers.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Approved Job Requirement Selection */}
        <Card className="border-t-4 border-t-[#001B4D]">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-[#005BBB]" />
              Select Approved Job Opportunity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Approved Job Requirement <span className="text-red-500">*</span>
              </label>
              <select
                {...register('job_requirement_id')}
                disabled={isLoadingJobs}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB] bg-white"
              >
                <option value="">-- Choose an Approved Job Requirement --</option>
                {approvedJobs.map((job: JobRequirementListItem) => (
                  <option key={job.id} value={job.id}>
                    {job.company_name} — {job.title} ({job.location})
                  </option>
                ))}
              </select>
              {errors.job_requirement_id && (
                <p className="text-xs text-red-600 mt-1">{errors.job_requirement_id.message}</p>
              )}
              {approvedJobs.length === 0 && !isLoadingJobs && (
                <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5" />
                  No approved job requirements available. JDs must pass Step 7 Placement Head sign-off first.
                </p>
              )}
            </div>

            {/* Approved Job Details Preview Card */}
            {selectedJob && (
              <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-lg text-sm text-slate-700 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-[#001B4D]">
                  <FileCheck className="w-4 h-4 text-emerald-600" />
                  Approved Opportunity: {selectedJob.title}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-slate-600 pt-1">
                  <div>
                    <span className="font-semibold text-slate-800">Employer:</span> {selectedJob.company_name}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800">Location:</span> {selectedJob.location}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800">Salary Package:</span> {selectedJob.min_salary} - {selectedJob.max_salary} LPA
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800">Registration Cutoff:</span>{' '}
                    {new Date(selectedJob.registration_deadline).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="font-semibold text-slate-800">5-Point Checklist:</span>{' '}
                    <span className="text-emerald-700 font-semibold">100% Verified</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Deliverable Specifications */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Palette className="w-5 h-5 text-[#005BBB]" />
              Deliverable Specifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Deliverable Format <span className="text-red-500">*</span>
                </label>
                <select
                  {...register('deliverable_type')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB] bg-white"
                >
                  <option value="COMBINED_PACK">Combined Creative Pack (Flyer, Banner & Social Post)</option>
                  <option value="FLYER">Placement Announcement Flyer (A4 / Document)</option>
                  <option value="BANNER">Web / Portal Display Banner</option>
                  <option value="SOCIAL_POST">Social Media Post (Square / WhatsApp / LinkedIn)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Production Priority <span className="text-red-500">*</span>
                </label>
                <select
                  {...register('priority')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB] bg-white"
                >
                  <option value="LOW">Low Priority</option>
                  <option value="MEDIUM">Medium Priority (Standard)</option>
                  <option value="HIGH">High Priority</option>
                  <option value="URGENT">Urgent — Immediate Drive Cutoff</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Request Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. Infosys 2026 Campus Drive Placement Flyer"
                {...register('title')}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              />
              {errors.title && <p className="text-xs text-red-600 mt-1">{errors.title.message}</p>}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Production Deadline
                </label>
                <input
                  type="datetime-local"
                  {...register('production_deadline')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Target Student Cohort
                </label>
                <input
                  type="text"
                  placeholder="e.g. 2026 Batch — CS, IS, EC Engineering"
                  {...register('target_audience')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Creative Brief & Design Instructions <span className="text-red-500">*</span>
              </label>
              <textarea
                rows={6}
                placeholder="Detail the key highlights, eligibility criteria, and visual instructions for the designer..."
                {...register('brief')}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB] font-mono text-xs"
              />
              {errors.brief && <p className="text-xs text-red-600 mt-1">{errors.brief.message}</p>}
            </div>
          </CardContent>
        </Card>

        {/* Verification Linkages (Step 9 Prerequisite Points) */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Info className="w-5 h-5 text-[#005BBB]" />
              Links & Contacts for 4-Point Checklist Verification
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Drive Registration URL
                </label>
                <input
                  type="url"
                  placeholder="https://placements.gqt.edu/register/infosys-2026"
                  {...register('registration_link')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
                {errors.registration_link && (
                  <p className="text-xs text-red-600 mt-1">{errors.registration_link.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  QR Code Destination URL
                </label>
                <input
                  type="url"
                  placeholder="https://placements.gqt.edu/register/infosys-2026"
                  {...register('qr_code_target_url')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
                {errors.qr_code_target_url && (
                  <p className="text-xs text-red-600 mt-1">{errors.qr_code_target_url.message}</p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Placement Cell Support Email
                </label>
                <input
                  type="email"
                  placeholder="placements@gqt.edu"
                  {...register('contact_email')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
                {errors.contact_email && (
                  <p className="text-xs text-red-600 mt-1">{errors.contact_email.message}</p>
                )}
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                  Placement Helpdesk Phone
                </label>
                <input
                  type="text"
                  placeholder="+91 98765 43210"
                  {...register('contact_phone')}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Error message */}
        {createMutation.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{(createMutation.error as Error)?.message || 'Failed to create creative request.'}</span>
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/creatives')}
            disabled={isSubmitting || createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || createMutation.isPending || approvedJobs.length === 0}
            className="bg-[#001B4D] hover:bg-[#002875] text-white flex items-center gap-2"
          >
            <Check className="w-4 h-4" />
            {createMutation.isPending ? 'Dispatching Request...' : 'Dispatch Creative Request'}
          </Button>
        </div>
      </form>
    </div>
  );
};
