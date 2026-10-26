import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, ArrowLeft, Check, ExternalLink } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { DuplicateMatch } from '../../types/crm';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';

const companySchema = z.object({
  name: z.string().min(2, 'Company legal or trading name is required (min 2 characters).'),
  website: z.string().url('Must be a valid URL (e.g. https://company.com)').or(z.literal('')).optional(),
  domain_category: z.string().min(1, 'Domain category is required.'),
  tier: z.string().min(1, 'Tier is required.'),
  relationship_status: z.string().min(1, 'Relationship status is required.'),
  source: z.string().min(1, 'Discovery source is required.'),
  city: z.string().optional(),
  state: z.string().optional(),
  country: z.string().default('India'),
  address: z.string().optional(),
  notes: z.string().optional(),
});

type CompanyFormData = z.infer<typeof companySchema>;

export const CompanyFormPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [duplicates, setDuplicates] = useState<DuplicateMatch[]>([]);
  const [checkingDuplicates, setCheckingDuplicates] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CompanyFormData>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      name: '',
      website: '',
      domain_category: 'IT_SERVICES',
      tier: 'TIER_2',
      relationship_status: 'DISCOVERED',
      source: 'MARKET_RESEARCH',
      city: '',
      state: '',
      country: 'India',
      address: '',
      notes: '',
    },
  });

  const watchName = watch('name');
  const watchWebsite = watch('website');

  // Load existing company if editing
  const { data: existingCompany, isLoading: loadingExisting } = useQuery({
    queryKey: ['company-detail', id],
    queryFn: () => (id ? crmApi.getCompany(id) : null),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existingCompany) {
      setValue('name', existingCompany.name);
      setValue('website', existingCompany.website || '');
      setValue('domain_category', existingCompany.domain_category);
      setValue('tier', existingCompany.tier);
      setValue('relationship_status', existingCompany.relationship_status);
      setValue('source', existingCompany.source);
      setValue('city', existingCompany.city || '');
      setValue('state', existingCompany.state || '');
      setValue('country', existingCompany.country || 'India');
      setValue('address', existingCompany.address || '');
      setValue('notes', existingCompany.notes || '');
    }
  }, [existingCompany, setValue]);

  // Live duplicate warning check
  useEffect(() => {
    if (isEdit || !watchName || watchName.trim().length < 3) {
      setDuplicates([]);
      return;
    }

    const timer = setTimeout(async () => {
      setCheckingDuplicates(true);
      try {
        const res = await crmApi.checkCompanyDuplicate(watchName.trim(), watchWebsite || undefined);
        setDuplicates(res.data || []);
      } catch {
        setDuplicates([]);
      } finally {
        setCheckingDuplicates(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [watchName, watchWebsite, isEdit]);

  const saveMutation = useMutation({
    mutationFn: (data: CompanyFormData) => {
      if (isEdit && id) {
        return crmApi.updateCompany(id, data);
      }
      return crmApi.createCompany(data);
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      navigate(`/crm/companies/${saved.id}`);
    },
  });

  const onSubmit = (formData: CompanyFormData) => {
    saveMutation.mutate(formData);
  };

  if (isEdit && loadingExisting) {
    return <LoadingState message="Loading company profile for edit..." />;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/crm/companies" className="p-1.5 rounded-lg border border-gqt-neutral-300 hover:bg-gqt-neutral-100">
            <ArrowLeft className="w-4 h-4 text-gqt-neutral-600" />
          </Link>
          <div>
            <h1 className="text-xl font-black text-gqt-navy">
              {isEdit ? `Edit Company: ${existingCompany?.name}` : 'Register New Corporate Company'}
            </h1>
            <p className="text-xs text-gqt-neutral-500 mt-0.5">
              Target company identification and industry classification (Workflow Step 1).
            </p>
          </div>
        </div>
      </div>

      {/* Duplicate Warning Alert Card */}
      {duplicates.length > 0 && (
        <Card className="p-4 bg-amber-50 border-amber-300">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1.5">
              <h3 className="text-sm font-bold text-amber-900">
                Potential Duplicate Company Detected ({duplicates.length} match{duplicates.length > 1 ? 'es' : ''})
              </h3>
              <p className="text-xs text-amber-800">
                The corporate directory already contains entity records with a matching normalized name or domain.
                Please review before creating a duplicate record:
              </p>
              <div className="divide-y divide-amber-200 mt-2 bg-white/70 rounded-lg p-2.5 border border-amber-200">
                {duplicates.map((dup) => (
                  <div key={dup.company_id} className="py-1.5 flex items-center justify-between text-xs">
                    <div>
                      <strong className="text-gqt-navy">{dup.name}</strong>{' '}
                      {dup.domain && <span className="text-gqt-neutral-500">({dup.domain})</span>} —{' '}
                      <span className="text-amber-800 italic">{dup.reason}</span>
                    </div>
                    <Link
                      to={`/crm/companies/${dup.company_id}`}
                      target="_blank"
                      className="text-gqt-blue hover:underline font-semibold flex items-center gap-0.5"
                    >
                      View Record <ExternalLink className="w-3 h-3" />
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Main Form */}
      <Card className="p-6">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Company Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
                Company Legal / Trading Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                {...register('name')}
                placeholder="e.g. Tata Consultancy Services Ltd."
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.name && <p className="text-[11px] text-red-600">{errors.name.message}</p>}
              {checkingDuplicates && <p className="text-[10px] text-gqt-neutral-400">Checking for duplicate records...</p>}
            </div>

            {/* Official Website */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
                Corporate Website (Optional)
              </label>
              <input
                type="text"
                {...register('website')}
                placeholder="https://www.tcs.com"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {errors.website && <p className="text-[11px] text-red-600">{errors.website.message}</p>}
            </div>

            {/* Domain / Industry Category */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
                Industry Domain Category <span className="text-red-500">*</span>
              </label>
              <select
                {...register('domain_category')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="IT_SERVICES">IT Services & Consulting</option>
                <option value="PRODUCT_TECH">Product & SaaS Technology</option>
                <option value="CORE_ENGINEERING">Core Engineering / Manufacturing</option>
                <option value="FINANCE_BANKING">Banking, Finance & Insurance (BFSI)</option>
                <option value="BPO_ITES">BPO / ITES / Operations</option>
                <option value="EDTECH">Education & EdTech</option>
                <option value="HEALTHCARE">Healthcare & Life Sciences</option>
                <option value="CONSULTING">Management Consulting</option>
                <option value="OTHER">Other Domain</option>
              </select>
            </div>

            {/* Company Tier */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Company Tier</label>
              <select
                {...register('tier')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="TIER_1">Tier 1 — Enterprise / MNC</option>
                <option value="TIER_2">Tier 2 — Mid-Market / Established</option>
                <option value="TIER_3">Tier 3 — Startup / Growth Stage</option>
              </select>
            </div>

            {/* Relationship Status */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Relationship Status</label>
              <select
                {...register('relationship_status')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="DISCOVERED">Discovered — Target Identified</option>
                <option value="OUTREACH_IN_PROGRESS">Outreach in Progress</option>
                <option value="CONNECTED">Connected — In Conversation</option>
                <option value="INTERESTED">Interested — Hiring Freshers</option>
                <option value="ACTIVE_HIRING_PARTNER">Active Hiring Partner</option>
                <option value="NOT_INTERESTED">Not Interested</option>
                <option value="ON_HOLD">On Hold</option>
              </select>
            </div>

            {/* Discovery Source */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Discovery Source</label>
              <select
                {...register('source')}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
              >
                <option value="MARKET_RESEARCH">Market Research</option>
                <option value="LINKEDIN">LinkedIn Research</option>
                <option value="REFERRAL">Corporate Referral</option>
                <option value="CAMPUS_INBOUND">Campus Inbound Lead</option>
                <option value="COLD_OUTREACH">Cold Outreach</option>
                <option value="JOB_BOARD">Job Board / Portal</option>
                <option value="OTHER">Other Channel</option>
              </select>
            </div>

            {/* City */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Headquarters / City</label>
              <input
                type="text"
                {...register('city')}
                placeholder="e.g. Bengaluru"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            {/* State */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">State</label>
              <input
                type="text"
                {...register('state')}
                placeholder="e.g. Karnataka"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
          </div>

          {/* Full Address */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Corporate Office Address</label>
            <textarea
              {...register('address')}
              rows={2}
              placeholder="Campus address, tech park name, SEZ details..."
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          {/* Internal Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Internal Relationship Notes</label>
            <textarea
              {...register('notes')}
              rows={3}
              placeholder="Context about past campus drives, eligibility criteria, fresher hiring timelines..."
              className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          {/* Error Message */}
          {saveMutation.isError && (
            <p className="text-xs text-red-600 font-semibold">
              {saveMutation.error instanceof Error ? saveMutation.error.message : 'Failed to save company profile.'}
            </p>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gqt-neutral-200">
            <Link to="/crm/companies">
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
              {isEdit ? 'Update Company Profile' : 'Save & Register Company'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
};
