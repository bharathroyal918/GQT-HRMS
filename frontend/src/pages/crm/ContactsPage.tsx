import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Users, Plus, Search, Building2, Mail, Phone, Archive, RotateCcw } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';

export const ContactsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['hr-contacts', { search, status, page }],
    queryFn: () =>
      crmApi.getHRContacts({
        search: search || undefined,
        status: status || undefined,
        page,
        page_size: 15,
      }),
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => crmApi.archiveHRContact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-contacts'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (id: string) => crmApi.restoreHRContact(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-contacts'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
    },
  });

  const handleArchive = (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to archive '${name}'? Historical outreach will remain intact.`)) {
      archiveMutation.mutate(id);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gqt-navy tracking-tight">HR Contact Directory</h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Directory of Corporate Talent Acquisition Leads and HR Decision Makers (Workflow Step 3).
          </p>
        </div>
        <Link to="/crm/contacts/new">
          <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
            New HR Contact
          </Button>
        </Link>
      </div>

      {/* Filter / Search Bar */}
      <Card className="p-4 bg-white">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="relative sm:col-span-2">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gqt-neutral-400" />
            <input
              type="text"
              placeholder="Search by contact name, company, email, phone, or designation..."
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
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Contact Statuses</option>
              <option value="ACTIVE">Active Recruiter</option>
              <option value="PROSPECT">Prospect Lead</option>
              <option value="INACTIVE">Inactive</option>
              <option value="BOUNCED_INVALID">Bounced / Invalid Details</option>
              <option value="LEFT_COMPANY">Left Company</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Content */}
      {isLoading ? (
        <LoadingState message="Loading HR contact directory..." />
      ) : error ? (
        <ErrorState
          title="Could not load HR contacts"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      ) : !data || data.data.length === 0 ? (
        <EmptyState
          title="No Contacts Found"
          description="No HR contact leads matched your criteria. Add HR contacts linked to target companies."
          action={
            <Link to="/crm/contacts/new">
              <Button size="sm" variant="primary">
                Add HR Contact
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
                  <th className="py-3 px-4">Contact Name</th>
                  <th className="py-3 px-4">Corporate Entity</th>
                  <th className="py-3 px-4">Designation</th>
                  <th className="py-3 px-4">Contact Details</th>
                  <th className="py-3 px-4">Preferred Channel</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gqt-neutral-100">
                {data.data.map((contact) => (
                  <tr key={contact.id} className="hover:bg-gqt-neutral-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-gqt-navy">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <div>
                          <span>{contact.name}</span>
                          {contact.department && (
                            <span className="block text-[11px] font-normal text-gqt-neutral-500">
                              {contact.department}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-gqt-charcoal">
                      <Link
                        to={`/crm/companies/${contact.company.id}`}
                        className="hover:text-gqt-blue flex items-center gap-1"
                      >
                        <Building2 className="w-3.5 h-3.5 text-gqt-neutral-400" />
                        {contact.company.name}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 text-gqt-neutral-600">{contact.designation || '—'}</td>
                    <td className="py-3.5 px-4 space-y-0.5 text-gqt-neutral-600">
                      {contact.email && (
                        <div className="flex items-center gap-1.5">
                          <Mail className="w-3 h-3 text-gqt-neutral-400" />
                          <a href={`mailto:${contact.email}`} className="text-gqt-blue hover:underline">
                            {contact.email}
                          </a>
                        </div>
                      )}
                      {contact.phone && (
                        <div className="flex items-center gap-1.5">
                          <Phone className="w-3 h-3 text-gqt-neutral-400" />
                          <span>{contact.phone}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-neutral-700">
                        {contact.preferred_channel}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          contact.status === 'ACTIVE'
                            ? 'bg-emerald-100 text-emerald-800'
                            : contact.status === 'PROSPECT'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gqt-neutral-200 text-gqt-neutral-700'
                        }`}
                      >
                        {contact.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1 whitespace-nowrap">
                      <Link to={`/crm/outreach/new?company_id=${contact.company.id}&contact_id=${contact.id}`}>
                        <Button size="sm" variant="ghost">
                          Outreach
                        </Button>
                      </Link>
                      {contact.is_archived ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Restore contact"
                          onClick={() => restoreMutation.mutate(contact.id)}
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-emerald-600" />
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          title="Archive contact"
                          onClick={() => handleArchive(contact.id, contact.name)}
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
