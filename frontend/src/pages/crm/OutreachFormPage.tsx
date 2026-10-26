import React, { useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Check, Info } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';

const outreachSchema = z.object({
  company: z.string().min(1, 'Target corporate company selection is required.'),
  hr_contact: z.string().optional(),
  channel: z.string().min(1, 'Channel is required.'),
  direction: z.string().default('OUTBOUND'),
  outcome: z.string().min(1, 'Activity outcome is required.'),
  subject: z.string().min(2, 'Concise business purpose summary is required.'),
  notes: z.string().optional(),
  followup_required: z.boolean().default(false),
});

type OutreachFormData = z.infer<typeof outreachSchema>;

export const OutreachFormPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const preCompanyId = searchParams.get('company_id') || '';
  const preContactId = searchParams.get('contact_id') || '';
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<OutreachFormData>({
    resolver: zodResolver(outreachSchema),
    defaultValues: {
      company: preCompanyId,
      hr_contact: preContactId,
      channel: 'CALL',
      direction: 'OUTBOUND',
      outcome: 'CONNECTED_INTERESTED',
      subject: '',
      notes: '',
      followup_required: false,
    },
  });

  const selectedCompanyId = watch('company');

  // Load companies for dropdown
  const { data: companiesData } = useQuery({
    queryKey: ['companies-dropdown'],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
  });

  // Load contacts for chosen company
  const { data: contactsData } = useQuery({
    queryKey: ['company-contacts-dropdown', selectedCompanyId],
    queryFn: () => (selectedCompanyId ? crmApi.getHRContacts({ company_id: selectedCompanyId, page_size: 50 }) : null),
    enabled: Boolean(selectedCompanyId),
  });

  useEffect(() => {
    if (preCompanyId) setValue('company', preCompanyId);
    if (preContactId) setValue('hr_contact', preContactId);
  }, [preCompanyId, preContactId, setValue]);

  const saveMutation = useMutation({
    mutationFn: (formData: OutreachFormData) => {
      const payload: Record<string, unknown> = {
        company: formData.company,
        channel: formData.channel,
        direction: formData.direction,
        outcome: formData.outcome,
        subject: formData.subject,
        notes: formData.notes || '',
        followup_required: formData.followup_required,
      };
      if (formData.hr_contact && formData.hr_contact.trim() !== '') {
        payload.hr_contact = formData.hr_contact;
      }
      return crmApi.createOutreachLog(payload);
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ['outreach-logs'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      queryClient.invalidateQueries({ queryKey: ['company-outreach', saved.company.id] });
      queryClient.invalidateQueries({ queryKey: ['company-detail', saved.company.id] });
      navigate('/crm/outreach');
    },
  });

  const onSubmit = (data: OutreachFormData) => {
    saveMutation.mutate(data);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/crm/outreach" className="p-1.5 rounded-lg border border-gqt-neutral-300 hover:bg-gqt-neutral-100">
          <ArrowLeft className="w-4 h-4 text-gqt-neutral-600" />
        </Link>
        <div>
          <h1 className="text-xl font-black text-gqt-navy">Log Corporate Outreach Touchpoint</h1>
          <p className="text-xs text-gqt-neutral-500 mt-0.5">
            Record actual interactions contributing toward the 100+ daily outreach operational benchmark (Workflow Step 2).
          </p>
        </div>
      </div>

      {/* Integration Boundary Notice */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-start gap-3 text-xs text-blue-900">
          <Info className="w-4 h-4 text-gqt-blue flex-shrink-0 mt-0.5" />
          <div>
            <strong>Activity Log Entry:</strong> This form records a completed communication touchpoint in the CRM audit trail.
            No external WhatsApp, email, or telephone messages will be automatically dispatched in this phase.
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Target Company */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
              Target Company <span className="text-red-500">*</span>
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

          {/* HR Contact (Filtered by chosen company) */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
              Specific HR Contact (Optional)
            </label>
            <select
              {...register('hr_contact')}
              disabled={!selectedCompanyId}
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white disabled:bg-gqt-neutral-100"
            >
              <option value="">
                {selectedCompanyId ? 'Company-level outreach (or select individual recruiter)' : 'Select a company first...'}
              </option>
              {contactsData?.data.map((contact) => (
                <option key={contact.id} value={contact.id}>
                  {contact.name} — {contact.designation || 'HR'} ({contact.email || contact.phone})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Channel */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Communication Channel</label>
              <select
                {...register('channel')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="CALL">Phone Call</option>
                <option value="EMAIL">Email</option>
                <option value="LINKEDIN">LinkedIn InMail</option>
                <option value="WHATSAPP">WhatsApp</option>
                <option value="IN_PERSON">In-Person Corporate Visit</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            {/* Direction */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Direction</label>
              <select
                {...register('direction')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="OUTBOUND">Outbound Outreach</option>
                <option value="INBOUND">Inbound Inquiry</option>
              </select>
            </div>

            {/* Outcome */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Activity Outcome</label>
              <select
                {...register('outcome')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="CONNECTED_INTERESTED">Connected — Interested in Hiring</option>
                <option value="CONNECTED_NOT_INTERESTED">Connected — Not Hiring Freshers</option>
                <option value="CONNECTED_CALL_LATER">Connected — Requested Callback</option>
                <option value="NO_ANSWER_BUSY">No Answer / Busy</option>
                <option value="INVALID_CONTACT_DETAILS">Invalid Contact Details</option>
                <option value="GATEKEEPER_BLOCKED">Gatekeeper / Operator Blocked</option>
                <option value="FOLLOW_UP_SCHEDULED">Follow-Up Scheduled</option>
                <option value="REQUIREMENT_COLLECTED">JD / Requirement Collected</option>
              </select>
            </div>
          </div>

          {/* Subject */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
              Business Purpose Summary <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              {...register('subject')}
              placeholder="e.g. Introduction of GQT 2026 Batch for Java Full Stack Roles"
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
            {errors.subject && <p className="text-[11px] text-red-600">{errors.subject.message}</p>}
          </div>

          {/* Detailed Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Conversation Notes</label>
            <textarea
              {...register('notes')}
              rows={3}
              placeholder="Key discussion points, eligibility criteria mentioned, proposed drive dates..."
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          {/* Follow-up Required */}
          <div className="flex items-center gap-2 pt-2">
            <input
              type="checkbox"
              id="followup_required"
              {...register('followup_required')}
              className="rounded border-gqt-neutral-300 text-gqt-blue focus:ring-gqt-blue"
            />
            <label htmlFor="followup_required" className="text-xs font-semibold text-gqt-navy cursor-pointer">
              Follow-up required for this corporate relationship
            </label>
          </div>

          {/* Error Message */}
          {saveMutation.isError && (
            <p className="text-xs text-red-600 font-semibold">
              {saveMutation.error instanceof Error ? saveMutation.error.message : 'Failed to record outreach activity.'}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gqt-neutral-200">
            <Link to="/crm/outreach">
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
              Record Outreach
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
