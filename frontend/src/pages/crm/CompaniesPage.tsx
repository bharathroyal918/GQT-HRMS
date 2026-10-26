import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Building2, Plus, Search, ExternalLink, Archive, RotateCcw } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';

export const CompaniesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [domainCategory, setDomainCategory] = useState('');
  const [relationshipStatus, setRelationshipStatus] = useState('');
  const [tier, setTier] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['companies', { search, domainCategory, relationshipStatus, tier, page }],
    queryFn: () =>
      crmApi.getCompanies({
        search: search || undefined,
        domain_category: domainCategory || undefined,
        relationship_status: relationshipStatus || undefined,
        tier: tier || undefined,
        page,
        page_size: 15,
      }),
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => crmApi.archiveCompany(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (id: string) => crmApi.restoreCompany(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
    },
  });

  const handleArchive = (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to archive '${name}'? Historical outreach will remain intact.`)) {
      archiveMutation.mutate(id);
    }
  };

  const handleRestore = (id: string) => {
    restoreMutation.mutate(id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Corporate Directory</h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Enterprise hiring partners categorized by industry domain and partnership status.
          </p>
        </div>
        <Link to="/crm/companies/new">
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
            New Company
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-white">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gqt-neutral-400" />
            <input
              type="text"
              placeholder="Search by name, domain, city..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          <div>
            <select
              value={domainCategory}
              onChange={(e) => {
                setDomainCategory(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Domains / Industries</option>
              <option value="IT_SERVICES">IT Services & Consulting</option>
              <option value="PRODUCT_TECH">Product & SaaS Technology</option>
              <option value="CORE_ENGINEERING">Core Engineering</option>
              <option value="FINANCE_BANKING">Banking, Finance & BFSI</option>
              <option value="BPO_ITES">BPO / ITES</option>
              <option value="EDTECH">EdTech & Education</option>
              <option value="HEALTHCARE">Healthcare & Life Sciences</option>
              <option value="CONSULTING">Consulting</option>
              <option value="OTHER">Other Domain</option>
            </select>
          </div>

          <div>
            <select
              value={relationshipStatus}
              onChange={(e) => {
                setRelationshipStatus(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Relationship Statuses</option>
              <option value="DISCOVERED">Discovered</option>
              <option value="OUTREACH_IN_PROGRESS">Outreach in Progress</option>
              <option value="CONNECTED">Connected</option>
              <option value="INTERESTED">Interested</option>
              <option value="ACTIVE_HIRING_PARTNER">Active Hiring Partner</option>
              <option value="NOT_INTERESTED">Not Interested</option>
              <option value="ON_HOLD">On Hold</option>
            </select>
          </div>

          <div>
            <select
              value={tier}
              onChange={(e) => {
                setTier(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Tiers</option>
              <option value="TIER_1">Tier 1 — Enterprise</option>
              <option value="TIER_2">Tier 2 — Mid-Market</option>
              <option value="TIER_3">Tier 3 — Startup</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Directory Content */}
      {isLoading ? (
        <LoadingState message="Loading companies..." />
      ) : error ? (
        <ErrorState
          title="Could not load company directory"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      ) : !data || data.data.length === 0 ? (
        <EmptyState
          title="No Companies Found"
          description="No enterprise profiles matched your filter criteria. Try adjusting your search."
          action={
            <Link to="/crm/companies/new">
              <Button size="sm" variant="primary">
                Add First Company
              </Button>
            </Link>
          }
        />
      ) : (
        <Card className="overflow-hidden border border-gqt-neutral-200">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-700 font-bold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Company Name</th>
                  <th className="py-3 px-4">Domain / Industry</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Tier</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4 text-center">HR Contacts</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gqt-neutral-100">
                {data.data.map((company) => (
                  <tr key={company.id} className="hover:bg-gqt-neutral-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-gqt-navy">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gqt-blue flex-shrink-0" />
                        <div>
                          <Link
                            to={`/crm/companies/${company.id}`}
                            className="hover:underline font-bold text-gqt-navy"
                          >
                            {company.name}
                          </Link>
                          {company.website && (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[11px] text-gqt-blue hover:underline flex items-center gap-0.5 mt-0.5"
                            >
                              {company.domain || company.website} <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-gqt-charcoal font-medium">
                      <span className="px-2 py-0.5 rounded text-[11px] bg-gqt-neutral-100 text-gqt-neutral-700">
                        {company.domain_category.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge
                        variant={
                          company.relationship_status === 'ACTIVE_HIRING_PARTNER'
                            ? 'success'
                            : company.relationship_status === 'CONNECTED' || company.relationship_status === 'INTERESTED'
                            ? 'info'
                            : company.relationship_status === 'NOT_INTERESTED'
                            ? 'danger'
                            : company.relationship_status === 'ON_HOLD'
                            ? 'warning'
                            : 'neutral'
                        }
                        label={company.relationship_status.replace(/_/g, ' ')}
                      />
                    </td>
                    <td className="py-3.5 px-4 text-gqt-neutral-600 font-medium">
                      {company.tier === 'TIER_1' ? 'Tier 1' : company.tier === 'TIER_2' ? 'Tier 2' : 'Tier 3'}
                    </td>
                    <td className="py-3.5 px-4 text-gqt-neutral-600">{company.city || '—'}</td>
                    <td className="py-3.5 px-4 text-center font-bold text-gqt-navy">
                      {company.hr_contacts_count}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1 whitespace-nowrap">
                      <Link to={`/crm/companies/${company.id}`}>
                        <Button size="sm" variant="ghost">
                          View
                        </Button>
                      </Link>
                      <Link to={`/crm/companies/${company.id}/edit`}>
                        <Button size="sm" variant="ghost">
                          Edit
                        </Button>
                      </Link>
                      {company.is_archived ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Restore company"
                          onClick={() => handleRestore(company.id)}
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-emerald-600" />
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Archive company"
                          onClick={() => handleArchive(company.id, company.name)}
                        >
                          <Archive className="w-3.5 h-3.5 text-gqt-neutral-400 hover:text-red-600" />
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.meta.total_pages > 1 && (
            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-between text-xs text-gqt-neutral-600">
              <div>
                Page {data.meta.current_page} of {data.meta.total_pages} ({data.meta.count} total)
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!data.meta.previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!data.meta.next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
