import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Briefcase,
  Building2,
  DollarSign,
  FileText,
  GraduationCap,
  ArrowLeft,
  CheckCircle,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { crmApi } from '@/api/crmApi';
import { Button } from '@/components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import { Input } from '@/components/common/Input';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

const jobFormSchema = z
  .object({
    company: z.string().min(1, 'Please select a company'),
    hr_contact: z.string().optional().nullable(),
    title: z.string().min(3, 'Role title must be at least 3 characters'),
    job_description: z.string().min(10, 'Job description must be at least 10 characters'),
    skills_required: z.string().min(3, 'Required skills must be specified'),
    min_salary: z.string().optional().nullable(),
    max_salary: z.string().optional().nullable(),
    salary_currency: z.string().default('INR'),
    salary_breakup: z.string().optional().default(''),
    location: z.string().min(2, 'Location is required'),
    work_arrangement: z.enum(['ON_SITE', 'HYBRID', 'REMOTE']),
    employment_type: z.enum(['FULL_TIME', 'INTERNSHIP', 'INTERNSHIP_PPO', 'CONTRACT']),
    has_bond: z.boolean().default(false),
    bond_details: z.string().optional().default(''),
    eligibility_criteria: z.string().optional().default(''),
    min_cgpa: z.string().optional().nullable(),
    hiring_process: z.string().optional().default(''),
    interview_date: z.string().optional().nullable(),
    registration_deadline: z.string().min(1, 'Registration deadline is required'),
    openings_count: z.coerce.number().min(1, 'At least 1 opening is required').default(1),
    notes: z.string().optional().default(''),
  })
  .refine(
    (data) => {
      if (data.min_salary && data.max_salary) {
        return parseFloat(data.min_salary) <= parseFloat(data.max_salary);
      }
      return true;
    },
    {
      message: 'Minimum salary cannot exceed maximum salary',
      path: ['min_salary'],
    }
  );

type JobFormValues = z.infer<typeof jobFormSchema>;

export const JobFormPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [selectedCompanyId, setSelectedCompanyId] = useState<string>('');
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch companies for dropdown
  const { data: companiesData } = useQuery({
    queryKey: ['companies-dropdown'],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
  });

  // Fetch HR contacts for selected company
  const { data: companyDetail } = useQuery({
    queryKey: ['company-detail', selectedCompanyId],
    queryFn: () => crmApi.getCompany(selectedCompanyId),
    enabled: Boolean(selectedCompanyId),
  });

  // Fetch existing job if in edit mode
  const {
    data: existingJob,
    isLoading: isLoadingJob,
    isError: isErrorJob,
  } = useQuery({
    queryKey: ['job-detail', id],
    queryFn: () => jobsApi.getJob(id!),
    enabled: isEdit,
  });

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<JobFormValues>({
    resolver: zodResolver(jobFormSchema),
    defaultValues: {
      work_arrangement: 'ON_SITE',
      employment_type: 'FULL_TIME',
      salary_currency: 'INR',
      has_bond: false,
      openings_count: 1,
    },
  });

  const hasBondWatch = watch('has_bond');
  const companyWatch = watch('company');

  useEffect(() => {
    if (companyWatch) {
      setSelectedCompanyId(companyWatch);
    }
  }, [companyWatch]);

  // Pre-fill form when editing
  useEffect(() => {
    if (existingJob) {
      setSelectedCompanyId(existingJob.company);
      reset({
        company: existingJob.company,
        hr_contact: existingJob.hr_contact || '',
        title: existingJob.title,
        job_description: existingJob.job_description,
        skills_required: existingJob.skills_required,
        min_salary: existingJob.min_salary || '',
        max_salary: existingJob.max_salary || '',
        salary_currency: existingJob.salary_currency || 'INR',
        salary_breakup: existingJob.salary_breakup || '',
        location: existingJob.location,
        work_arrangement: existingJob.work_arrangement,
        employment_type: existingJob.employment_type,
        has_bond: existingJob.has_bond,
        bond_details: existingJob.bond_details || '',
        eligibility_criteria: existingJob.eligibility_criteria || '',
        min_cgpa: existingJob.min_cgpa || '',
        hiring_process: existingJob.hiring_process || '',
        interview_date: existingJob.interview_date || '',
        registration_deadline: existingJob.registration_deadline
          ? existingJob.registration_deadline.slice(0, 16)
          : '',
        openings_count: existingJob.openings_count || 1,
        notes: existingJob.notes || '',
      });
    }
  }, [existingJob, reset]);

  const mutation = useMutation({
    mutationFn: (data: JobFormValues) => {
      const payload: Record<string, unknown> = {
        ...data,
        min_salary: data.min_salary ? parseFloat(data.min_salary) : null,
        max_salary: data.max_salary ? parseFloat(data.max_salary) : null,
        min_cgpa: data.min_cgpa ? parseFloat(data.min_cgpa) : null,
        hr_contact: data.hr_contact || null,
        interview_date: data.interview_date || null,
      };

      if (isEdit) {
        return jobsApi.updateJob(id!, payload);
      }
      return jobsApi.createJob(payload);
    },
    onSuccess: (savedJob) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['job-metrics'] });
      navigate(`/jobs/${savedJob.id}`);
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.error?.message ||
        err?.response?.data?.detail ||
        'Failed to save job requirement. Please verify all fields.';
      setFormError(msg);
    },
  });

  const onSubmit = (values: JobFormValues) => {
    setFormError(null);
    mutation.mutate(values);
  };

  if (isEdit && isLoadingJob) {
    return <LoadingState message="Loading job requirement..." />;
  }

  if (isEdit && isErrorJob) {
    return (
      <ErrorState
        title="Error Loading Requirement"
        message="Could not load the specified job requirement."
        onRetry={() => navigate('/jobs')}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-gqt-neutral-600 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Job Requirements
        </Link>
        <span className="text-xs text-gqt-neutral-500 font-mono">
          Workflow Step 5: Collect Job Description
        </span>
      </div>

      <div className="border-b border-gqt-neutral-200 pb-4">
        <h1 className="text-2xl font-bold text-gqt-navy flex items-center gap-2">
          <Briefcase className="w-6 h-6 text-gqt-blue" />
          {isEdit ? 'Edit Job Requirement' : 'Corporate Job Description Intake'}
        </h1>
        <p className="text-sm text-gqt-neutral-600 mt-1">
          {isEdit
            ? 'Update job details before submitting for checklist verification.'
            : 'Capture the complete role requirements, eligibility criteria, and drive dates. Upon creation, the 5-point verification checklist is initialized.'}
        </p>
      </div>

      {formError && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm">
          {formError}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Section 1: Corporate Partner & Contact */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Building2 className="w-5 h-5 text-gqt-blue" />
              1. Corporate Partner & Source
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Corporate Company <span className="text-rose-500">*</span>
                </label>
                <select
                  {...register('company')}
                  disabled={isEdit}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="">Select Corporate Company</option>
                  {companiesData?.data?.map((comp) => (
                    <option key={comp.id} value={comp.id}>
                      {comp.name} ({comp.tier})
                    </option>
                  ))}
                </select>
                {errors.company && (
                  <p className="text-xs text-rose-600 mt-1">{errors.company.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Corporate HR Contact (Optional)
                </label>
                <select
                  {...register('hr_contact')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="">Select HR Lead / Contact</option>
                  {companyDetail?.hr_contacts?.map((contact) => (
                    <option key={contact.id} value={contact.id}>
                      {contact.name} — {contact.designation || 'HR'} ({contact.email || contact.phone})
                    </option>
                  ))}
                </select>
                {errors.hr_contact && (
                  <p className="text-xs text-rose-600 mt-1">{errors.hr_contact.message}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 2: Role Details & Scope */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5 text-gqt-blue" />
              2. Role Specifications & Overview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Input
                  label="Role Title / Designation *"
                  placeholder="e.g. Associate Software Engineer — Full Stack"
                  {...register('title')}
                  error={errors.title?.message}
                />
              </div>

              <div>
                <Input
                  label="Primary Location *"
                  placeholder="e.g. Bangalore / Hyderabad"
                  {...register('location')}
                  error={errors.location?.message}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Work Arrangement *
                </label>
                <select
                  {...register('work_arrangement')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="ON_SITE">On-Site Office / Campus</option>
                  <option value="HYBRID">Hybrid (Office & Remote)</option>
                  <option value="REMOTE">100% Remote / Work from Home</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Employment Type *
                </label>
                <select
                  {...register('employment_type')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="FULL_TIME">Full-Time Employment</option>
                  <option value="INTERNSHIP">Internship Only</option>
                  <option value="INTERNSHIP_PPO">Internship + Full-Time PPO</option>
                  <option value="CONTRACT">Fixed-Term Contract</option>
                </select>
              </div>

              <div>
                <Input
                  label="Openings Count *"
                  type="number"
                  min="1"
                  {...register('openings_count')}
                  error={errors.openings_count?.message}
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                Detailed Job Description & Responsibilities *
              </label>
              <textarea
                rows={5}
                placeholder="Comprehensive description of role responsibilities, team structure, and day-to-day deliverables..."
                {...register('job_description')}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.job_description && (
                <p className="text-xs text-rose-600 mt-1">{errors.job_description.message}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                Required Technical & Functional Skills *
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Java 17, Spring Boot, PostgreSQL, Data Structures & Algorithms, REST APIs, Git"
                {...register('skills_required')}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.skills_required && (
                <p className="text-xs text-rose-600 mt-1">{errors.skills_required.message}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Compensation & Service Terms */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-gqt-blue" />
              3. Compensation Package & Service Terms
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Input
                  label="Minimum Annual Salary (INR)"
                  type="number"
                  placeholder="e.g. 500000"
                  {...register('min_salary')}
                  error={errors.min_salary?.message}
                />
              </div>

              <div>
                <Input
                  label="Maximum Annual Salary (INR)"
                  type="number"
                  placeholder="e.g. 750000"
                  {...register('max_salary')}
                  error={errors.max_salary?.message}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Currency
                </label>
                <select
                  {...register('salary_currency')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="INR">INR (₹)</option>
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                Salary Structure & Benefits Breakup
              </label>
              <textarea
                rows={2}
                placeholder="e.g. Fixed: ₹5.5 LPA, Performance Bonus: ₹1 LPA, Training Stipend: ₹25,000/month during 3-month probation."
                {...register('salary_breakup')}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            <div className="pt-2 border-t border-gqt-neutral-100 space-y-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="has_bond"
                  {...register('has_bond')}
                  className="w-4 h-4 text-gqt-blue rounded border-gqt-neutral-300 focus:ring-gqt-blue"
                />
                <label htmlFor="has_bond" className="text-sm font-semibold text-gqt-navy">
                  Service Agreement / Bond Required
                </label>
              </div>

              {hasBondWatch && (
                <div className="pl-6">
                  <Input
                    label="Service Agreement Duration & Penalty Terms"
                    placeholder="e.g. 18-month service agreement with ₹1,00,000 training recovery clause."
                    {...register('bond_details')}
                    error={errors.bond_details?.message}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Section 4: Eligibility & Drive Schedule */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-gqt-blue" />
              4. Candidate Eligibility & Drive Timelines
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Input
                  label="Minimum CGPA Cutoff (Scale of 10.0)"
                  type="number"
                  step="0.01"
                  placeholder="e.g. 6.50"
                  {...register('min_cgpa')}
                  error={errors.min_cgpa?.message}
                />
              </div>

              <div>
                <Input
                  label="Tentative Interview / Drive Date"
                  type="date"
                  {...register('interview_date')}
                  error={errors.interview_date?.message}
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Academic Eligibility Criteria Details
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. B.Tech / BE (CSE, IT, ECE, EEE), MCA, MSc (CS) from 2024 & 2025 batches. 60%+ in 10th, 12th & Graduation. Max 1 active backlog allowed at time of interview."
                  {...register('eligibility_criteria')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase tracking-wide mb-1">
                  Selection & Interview Process Stages
                </label>
                <textarea
                  rows={2}
                  placeholder="e.g. Round 1: Online Aptitude & Coding (60 min), Round 2: Technical Interview 1 (DSA & System Design), Round 3: Technical Interview 2, Round 4: HR Discussion & Offer."
                  {...register('hiring_process')}
                  className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              <div className="md:col-span-2">
                <Input
                  label="Registration Deadline Cutoff (Date & Time) *"
                  type="datetime-local"
                  {...register('registration_deadline')}
                  error={errors.registration_deadline?.message}
                />
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Students will not be permitted to apply or register after this timestamp.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gqt-neutral-200">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/jobs')}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            isLoading={mutation.isPending}
            leftIcon={<CheckCircle className="w-4 h-4" />}
          >
            {isEdit ? 'Save Changes' : 'Save & Initialize 5-Point Verification'}
          </Button>
        </div>
      </form>
    </div>
  );
};
