import React, { useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Check } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';

const contactSchema = z.object({
  company: z.string().min(1, 'Target corporate company selection is required.'),
  name: z.string().min(2, 'Contact full name is required (min 2 characters).'),
  designation: z.string().optional(),
  department: z.string().default('Human Resources'),
  email: z.string().email('Valid corporate email address required').or(z.literal('')).optional(),
  phone: z.string().optional(),
  alt_phone: z.string().optional(),
  linkedin_url: z.string().url('Must be a valid URL (e.g. https://linkedin.com/in/...)').or(z.literal('')).optional(),
  preferred_channel: z.string().default('CALL'),
  status: z.string().default('ACTIVE'),
  notes: z.string().optional(),
});

type ContactFormData = z.infer<typeof contactSchema>;

export const ContactFormPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preselectedCompanyId = searchParams.get('company_id') || '';
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: companiesData } = useQuery({
    queryKey: ['companies-list-dropdown'],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
  });

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      company: preselectedCompanyId,
      name: '',
      designation: 'Campus Recruiter',
      department: 'Human Resources',
      email: '',
      phone: '',
      alt_phone: '',
      linkedin_url: '',
      preferred_channel: 'CALL',
      status: 'ACTIVE',
      notes: '',
    },
  });

  useEffect(() => {
    if (preselectedCompanyId) {
      setValue('company', preselectedCompanyId);
    }
  }, [preselectedCompanyId, setValue]);

  const saveMutation = useMutation({
    mutationFn: (data: ContactFormData) => crmApi.createHRContact(data),
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ['hr-contacts'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['company-detail', saved.company.id] });
      navigate('/crm/contacts');
    },
  });

  const onSubmit = (formData: ContactFormData) => {
    saveMutation.mutate(formData);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/crm/contacts" className="p-1.5 rounded-lg border border-gqt-neutral-300 hover:bg-gqt-neutral-100">
          <ArrowLeft className="w-4 h-4 text-gqt-neutral-600" />
        </Link>
        <div>
          <h1 className="text-xl font-black text-gqt-navy">Register HR Recruiter / Contact</h1>
          <p className="text-xs text-gqt-neutral-500 mt-0.5">
            Capture Corporate HR talent details for campus placement drives (Workflow Step 3).
          </p>
        </div>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Target Company */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
              Associated Company <span className="text-red-500">*</span>
            </label>
            <select
              {...register('company')}
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
            >
              <option value="">Select Target Company...</option>
              {companiesData?.data.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.domain_category.replace(/_/g, ' ')})
                </option>
              ))}
            </select>
            {errors.company && <p className="text-[11px] text-red-600">{errors.company.message}</p>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Contact Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                {...register('name')}
                placeholder="e.g. Priya Sharma"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.name && <p className="text-[11px] text-red-600">{errors.name.message}</p>}
            </div>

            {/* Designation */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Designation / Role</label>
              <input
                type="text"
                {...register('designation')}
                placeholder="e.g. Lead Talent Acquisition Partner"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            {/* Department */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Department</label>
              <input
                type="text"
                {...register('department')}
                placeholder="Human Resources / University Relations"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            {/* Work Email */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Corporate Email</label>
              <input
                type="email"
                {...register('email')}
                placeholder="priya.sharma@company.com"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.email && <p className="text-[11px] text-red-600">{errors.email.message}</p>}
            </div>

            {/* Work Phone */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Primary Phone</label>
              <input
                type="text"
                {...register('phone')}
                placeholder="+91 98765 43210"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            {/* Preferred Channel */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Preferred Channel</label>
              <select
                {...register('preferred_channel')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="CALL">Phone Call</option>
                <option value="EMAIL">Email Communication</option>
                <option value="LINKEDIN">LinkedIn Message</option>
                <option value="WHATSAPP">WhatsApp Business</option>
                <option value="IN_PERSON">In-Person Corporate Visit</option>
              </select>
            </div>

            {/* LinkedIn URL */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">LinkedIn Profile URL</label>
              <input
                type="text"
                {...register('linkedin_url')}
                placeholder="https://linkedin.com/in/username"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.linkedin_url && <p className="text-[11px] text-red-600">{errors.linkedin_url.message}</p>}
            </div>

            {/* Contact Status */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Contact Status</label>
              <select
                {...register('status')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="ACTIVE">Active Recruiter</option>
                <option value="PROSPECT">Prospect Lead</option>
                <option value="INACTIVE">Inactive</option>
                <option value="BOUNCED_INVALID">Bounced / Invalid Details</option>
                <option value="LEFT_COMPANY">Left Company</option>
              </select>
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Contact Notes</label>
            <textarea
              {...register('notes')}
              rows={3}
              placeholder="Fresher hiring preferences, communication availability, best time to call..."
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          {/* Error Message */}
          {saveMutation.isError && (
            <p className="text-xs text-red-600 font-semibold">
              {saveMutation.error instanceof Error ? saveMutation.error.message : 'Failed to register HR contact.'}
            </p>
          )}

          {/* Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gqt-neutral-200">
            <Link to="/crm/contacts">
              <Button type="button" variant="outline" size="sm">
                Cancel
              </Button>
            </Link>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={saveMutation.isPending}
              leftIcon={<Check className="w-4 h-4" />}
            >
              Save Contact
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
