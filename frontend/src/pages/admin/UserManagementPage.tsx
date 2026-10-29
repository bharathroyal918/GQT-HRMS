import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Navigate } from 'react-router-dom';
import {
  Users,
  UserPlus,
  ShieldCheck,
  Search,
  Edit2,
  History,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  X,
  Phone,
  Mail,
  Clock,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { usersApi } from '@/api/usersApi';
import {
  User,
  UserCreatePayload,
  UserUpdatePayload,
  UserAuditLog,
} from '@/types/admin';
import { Card, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

export const UserManagementPage: React.FC = () => {
  const { user: currentUser, isLoading: isAuthLoading, hasRole } = useAuth();
  const isAdmin = Boolean(currentUser?.is_superuser || hasRole('ADMIN'));
  const queryClient = useQueryClient();

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<'active' | 'inactive' | ''>('');
  const [selectedOrdering, setSelectedOrdering] = useState('-created_at');
  const [currentPage, setCurrentPage] = useState(1);

  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [roleManagingUser, setRoleManagingUser] = useState<User | null>(null);
  const [statusConfirmUser, setStatusConfirmUser] = useState<User | null>(null);
  const [auditViewingUser, setAuditViewingUser] = useState<User | null>(null);

  // Notification banners
  const [successBanner, setSuccessBanner] = useState<string | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Form states for modals
  const [createForm, setCreateForm] = useState<UserCreatePayload>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone_number: '',
    roles: [],
    is_active: true,
  });
  const [editForm, setEditForm] = useState<UserUpdatePayload>({
    first_name: '',
    last_name: '',
    phone_number: '',
  });
  const [selectedRoleCodes, setSelectedRoleCodes] = useState<string[]>([]);
  const [modalFormError, setModalFormError] = useState<string | null>(null);

  // 1. Fetch Users Query
  const {
    data: usersResponse,
    isLoading: isUsersLoading,
    error: usersError,
    refetch: refetchUsers,
  } = useQuery({
    queryKey: [
      'admin-users',
      searchTerm,
      selectedRole,
      selectedStatus,
      selectedOrdering,
      currentPage,
    ],
    queryFn: () =>
      usersApi.listUsers({
        search: searchTerm || undefined,
        role: selectedRole || undefined,
        status: selectedStatus || undefined,
        ordering: selectedOrdering || undefined,
        page: currentPage,
        page_size: 20,
      }),
    enabled: isAdmin,
  });

  // 2. Fetch Authoritative Roles Catalog
  const { data: roles = [] } = useQuery({
    queryKey: ['authoritative-roles'],
    queryFn: () => usersApi.listRoles(),
    enabled: isAdmin,
  });

  // 3. Fetch Audit Logs Query (only when audit modal is open)
  const [auditPage, setAuditPage] = useState(1);
  const { data: auditResponse, isLoading: isAuditLoading } = useQuery({
    queryKey: ['user-audit-logs', auditViewingUser?.id, auditPage],
    queryFn: () =>
      auditViewingUser ? usersApi.getUserAuditLogs(auditViewingUser.id, auditPage) : null,
    enabled: Boolean(auditViewingUser),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (payload: UserCreatePayload) => usersApi.createUser(payload),
    onSuccess: (createdUser: User) => {
      setSuccessBanner(`User account for ${createdUser.email} has been provisioned successfully.`);
      setErrorBanner(null);
      setIsCreateModalOpen(false);
      setCreateForm({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone_number: '',
        roles: [],
        is_active: true,
      });
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.email?.[0] ||
        err?.response?.data?.password?.[0] ||
        err?.response?.data?.detail ||
        err?.message ||
        'Failed to provision user account.';
      setModalFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UserUpdatePayload }) =>
      usersApi.updateUser(id, payload),
    onSuccess: (updatedUser: User) => {
      setSuccessBanner(`Profile details for ${updatedUser.email} updated successfully.`);
      setErrorBanner(null);
      setEditingUser(null);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.phone_number?.[0] ||
        err?.message ||
        'Failed to update user profile.';
      setModalFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const rolesMutation = useMutation({
    mutationFn: ({ id, roleCodes }: { id: string; roleCodes: string[] }) =>
      usersApi.assignUserRoles(id, { role_codes: roleCodes }),
    onSuccess: (data: { roles: string[] }) => {
      setSuccessBanner(
        `Role assignments synchronized successfully: ${data.roles.join(', ') || 'No roles'}.`
      );
      setErrorBanner(null);
      setRoleManagingUser(null);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.role_codes?.[0] ||
        err?.message ||
        'Failed to update user roles.';
      setModalFormError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      usersApi.updateUserStatus(id, { is_active: isActive }),
    onSuccess: (updatedUser: User) => {
      setSuccessBanner(
        `Account for ${updatedUser.email} is now ${updatedUser.is_active ? 'ACTIVE' : 'DEACTIVATED'
        }.`
      );
      setErrorBanner(null);
      setStatusConfirmUser(null);
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.[0] ||
        err?.message ||
        'Failed to update user account status.';
      setErrorBanner(typeof msg === 'string' ? msg : JSON.stringify(msg));
      setStatusConfirmUser(null);
    },
  });

  // Handlers to open modals
  const handleOpenEdit = (userToEdit: User) => {
    setModalFormError(null);
    setEditForm({
      first_name: userToEdit.first_name || '',
      last_name: userToEdit.last_name || '',
      phone_number: userToEdit.phone_number || '',
    });
    setEditingUser(userToEdit);
  };

  const handleOpenRoles = (userToManage: User) => {
    setModalFormError(null);
    setSelectedRoleCodes([...userToManage.roles]);
    setRoleManagingUser(userToManage);
  };

  const handleOpenStatusConfirm = (userToToggle: User) => {
    setErrorBanner(null);
    setStatusConfirmUser(userToToggle);
  };

  const handleOpenAudit = (userToAudit: User) => {
    setAuditPage(1);
    setAuditViewingUser(userToAudit);
  };

  // Redirect unauthorized accounts
  if (!isAuthLoading && !isAdmin) {
    return <Navigate to="/access-denied" replace />;
  }

  if (isAuthLoading || (isUsersLoading && !usersResponse)) {
    return (
      <div className="py-12">
        <LoadingState message="Loading platform users and role directory..." />
      </div>
    );
  }

  if (usersError) {
    return (
      <div className="py-12">
        <ErrorState
          title="Unable to load User Directory"
          message="An error occurred communicating with the server while retrieving user accounts."
          onRetry={() => refetchUsers()}
        />
      </div>
    );
  }

  const usersList = usersResponse?.data || [];
  const meta = usersResponse?.meta;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
              System Administration
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gqt-navy mt-1 flex items-center gap-2.5">
            <Users className="w-7 h-7 text-gqt-blue" />
            User & Role Administration
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Manage authenticated users, operational role assignments, profile data, and security audit history.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={() => {
              setModalFormError(null);
              setIsCreateModalOpen(true);
            }}
            leftIcon={<UserPlus className="w-4 h-4" />}
            className="bg-gqt-navy hover:bg-gqt-navy-light text-white text-xs"
          >
            Provision User Account
          </Button>
        </div>
      </div>

      {/* Global Success Banner */}
      {successBanner && (
        <div
          role="status"
          className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900 flex items-start justify-between gap-3 shadow-xs animate-fadeIn"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <p className="text-sm font-medium">{successBanner}</p>
          </div>
          <button
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs p-1"
            aria-label="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Global Error Banner */}
      {errorBanner && (
        <div
          role="alert"
          className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 flex items-start justify-between gap-3 shadow-xs animate-fadeIn"
        >
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <p className="text-sm font-medium">{errorBanner}</p>
          </div>
          <button
            onClick={() => setErrorBanner(null)}
            className="text-rose-700 hover:text-rose-900 text-xs p-1"
            aria-label="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Filters and Controls Card */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-gqt-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search by name, email, phone..."
                aria-label="Search users"
                className="w-full pl-9 pr-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal placeholder:text-gqt-neutral-400 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gqt-neutral-400 hover:text-gqt-charcoal text-xs"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Role Filter Dropdown */}
            <div>
              <select
                value={selectedRole}
                onChange={(e) => {
                  setSelectedRole(e.target.value);
                  setCurrentPage(1);
                }}
                aria-label="Filter by role"
                className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="">All Operational Roles</option>
                {roles.map((r) => (
                  <option key={r.code} value={r.code}>
                    {r.name} ({r.code})
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter Dropdown */}
            <div>
              <select
                value={selectedStatus}
                onChange={(e) => {
                  setSelectedStatus(e.target.value as any);
                  setCurrentPage(1);
                }}
                aria-label="Filter by account status"
                className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="">All Account Statuses</option>
                <option value="active">Active Accounts Only</option>
                <option value="inactive">Deactivated Accounts Only</option>
              </select>
            </div>

            {/* Sort Dropdown */}
            <div>
              <select
                value={selectedOrdering}
                onChange={(e) => {
                  setSelectedOrdering(e.target.value);
                  setCurrentPage(1);
                }}
                aria-label="Sort users"
                className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="-created_at">Joined: Newest First</option>
                <option value="created_at">Joined: Oldest First</option>
                <option value="email">Email: A to Z</option>
                <option value="-email">Email: Z to A</option>
                <option value="first_name">First Name: A to Z</option>
                <option value="-last_login">Last Login: Most Recent</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Directory Table */}
      {usersList.length === 0 ? (
        <EmptyState
          title="No Users Found"
          description="No user accounts match the selected search keywords or filter criteria."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchTerm('');
                setSelectedRole('');
                setSelectedStatus('');
                setSelectedOrdering('-created_at');
                setCurrentPage(1);
              }}
            >
              Reset All Filters
            </Button>
          }
        />
      ) : (
        <Card className="overflow-hidden border border-gqt-neutral-200">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gqt-charcoal">
              <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-600 uppercase font-semibold">
                <tr>
                  <th scope="col" className="px-4 py-3.5">
                    User Account
                  </th>
                  <th scope="col" className="px-4 py-3.5">
                    Phone
                  </th>
                  <th scope="col" className="px-4 py-3.5">
                    Operational Roles
                  </th>
                  <th scope="col" className="px-4 py-3.5">
                    Status
                  </th>
                  <th scope="col" className="px-4 py-3.5">
                    Last Login
                  </th>
                  <th scope="col" className="px-4 py-3.5 text-right">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gqt-neutral-100 bg-white">
                {usersList.map((usr) => {
                  const isCurrentLoggedUser = usr.id === currentUser?.id;
                  return (
                    <tr
                      key={usr.id}
                      className="hover:bg-gqt-neutral-50/60 transition-colors"
                    >
                      {/* Name & Email */}
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-gqt-navy flex items-center gap-1.5">
                          {usr.full_name}
                          {usr.is_superuser && (
                            <span className="text-[10px] bg-purple-100 text-purple-800 font-semibold px-1.5 py-0.2 rounded border border-purple-200">
                              SUPERUSER
                            </span>
                          )}
                          {isCurrentLoggedUser && (
                            <span className="text-[10px] bg-blue-100 text-blue-800 font-semibold px-1.5 py-0.2 rounded border border-blue-200">
                              YOU
                            </span>
                          )}
                        </div>
                        <div className="text-gqt-neutral-500 font-mono text-[11px] flex items-center gap-1 mt-0.5">
                          <Mail className="w-3 h-3 text-gqt-neutral-400" />
                          {usr.email}
                        </div>
                      </td>

                      {/* Phone */}
                      <td className="px-4 py-3.5 text-gqt-neutral-600">
                        {usr.phone_number ? (
                          <span className="flex items-center gap-1">
                            <Phone className="w-3 h-3 text-gqt-neutral-400" />
                            {usr.phone_number}
                          </span>
                        ) : (
                          <span className="text-gqt-neutral-400 italic">—</span>
                        )}
                      </td>

                      {/* Roles Badges */}
                      <td className="px-4 py-3.5">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {usr.roles.length > 0 ? (
                            usr.roles.map((roleCode) => (
                              <span
                                key={roleCode}
                                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${roleCode === 'ADMIN'
                                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                                  : roleCode === 'STUDENT'
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : 'bg-blue-50 text-blue-700 border-blue-200'
                                  }`}
                              >
                                {roleCode}
                              </span>
                            ))
                          ) : (
                            <span className="text-gqt-neutral-400 italic text-[11px]">
                              No roles assigned
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Account Status Badge */}
                      <td className="px-4 py-3.5">
                        <StatusBadge
                          variant={usr.is_active ? 'success' : 'danger'}
                          label={usr.is_active ? 'Active' : 'Deactivated'}
                        />
                      </td>

                      {/* Last Login */}
                      <td className="px-4 py-3.5 text-gqt-neutral-500 text-[11px]">
                        {usr.last_login ? (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-gqt-neutral-400" />
                            {new Date(usr.last_login).toLocaleDateString()}
                          </span>
                        ) : (
                          <span className="italic text-gqt-neutral-400">Never logged in</span>
                        )}
                      </td>

                      {/* Action Buttons */}
                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Edit Details */}
                          <button
                            onClick={() => handleOpenEdit(usr)}
                            title="Edit user profile"
                            aria-label={`Edit ${usr.email}`}
                            className="p-1.5 text-gqt-neutral-600 hover:text-gqt-blue hover:bg-gqt-neutral-100 rounded-md transition-colors"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>

                          {/* Manage Roles */}
                          <button
                            onClick={() => handleOpenRoles(usr)}
                            title="Manage operational roles"
                            aria-label={`Manage roles for ${usr.email}`}
                            className="p-1.5 text-gqt-neutral-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-md transition-colors"
                          >
                            <ShieldCheck className="w-4 h-4" />
                          </button>

                          {/* Toggle Active / Deactivate */}
                          <button
                            onClick={() => handleOpenStatusConfirm(usr)}
                            title={usr.is_active ? 'Deactivate account' : 'Activate account'}
                            aria-label={`${usr.is_active ? 'Deactivate' : 'Activate'} ${usr.email}`}
                            disabled={isCurrentLoggedUser && usr.is_active}
                            className={`p-1.5 rounded-md transition-colors ${usr.is_active
                              ? 'text-gqt-neutral-600 hover:text-rose-700 hover:bg-rose-50'
                              : 'text-gqt-neutral-600 hover:text-emerald-700 hover:bg-emerald-50'
                              } ${isCurrentLoggedUser && usr.is_active ? 'opacity-30 cursor-not-allowed' : ''}`}
                          >
                            {usr.is_active ? (
                              <XCircle className="w-4 h-4" />
                            ) : (
                              <CheckCircle2 className="w-4 h-4" />
                            )}
                          </button>

                          {/* Audit History */}
                          <button
                            onClick={() => handleOpenAudit(usr)}
                            title="View security audit trail"
                            aria-label={`View audit logs for ${usr.email}`}
                            className="p-1.5 text-gqt-neutral-600 hover:text-gqt-navy hover:bg-gqt-neutral-100 rounded-md transition-colors"
                          >
                            <History className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer */}
          {meta && meta.total_pages > 1 && (
            <div className="p-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gqt-neutral-600">
              <div>
                Showing page <strong className="text-gqt-charcoal">{meta.current_page}</strong> of{' '}
                <strong className="text-gqt-charcoal">{meta.total_pages}</strong> ({meta.count} total accounts)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                  disabled={!meta.previous}
                  className="text-xs"
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentPage((p) => p + 1)}
                  disabled={!meta.next}
                  className="text-xs"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* 1. Provision User Account Modal */}
      {isCreateModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="create-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-gqt-neutral-200 max-h-[90vh] flex flex-col">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="create-modal-title" className="text-base font-bold">
                  Provision User Account
                </h3>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal overflow-y-auto">
              {modalFormError && (
                <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{modalFormError}</span>
                </div>
              )}

              {/* Email */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">
                  Email Address <span className="text-rose-600">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={createForm.email}
                  onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                  placeholder="employee@gqt.local"
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Password */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">
                  Initial Password <span className="text-rose-600">*</span>
                </label>
                <input
                  type="password"
                  required
                  value={createForm.password}
                  onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })}
                  placeholder="Strong initial password"
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
                <p className="text-[11px] text-gqt-neutral-500">
                  Password must satisfy security complexity standards (at least 8 characters, non-common).
                </p>
              </div>

              {/* Names */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-gqt-charcoal">First Name</label>
                  <input
                    type="text"
                    value={createForm.first_name}
                    onChange={(e) => setCreateForm({ ...createForm, first_name: e.target.value })}
                    placeholder="First name"
                    className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-gqt-charcoal">Last Name</label>
                  <input
                    type="text"
                    value={createForm.last_name}
                    onChange={(e) => setCreateForm({ ...createForm, last_name: e.target.value })}
                    placeholder="Last name"
                    className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                  />
                </div>
              </div>

              {/* Phone */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">Phone Number</label>
                <input
                  type="tel"
                  value={createForm.phone_number}
                  onChange={(e) => setCreateForm({ ...createForm, phone_number: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Roles Selection */}
              <div className="space-y-2 pt-2 border-t border-gqt-neutral-200">
                <label className="font-semibold text-gqt-charcoal">
                  Assign Initial Operational Roles
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200 max-h-40 overflow-y-auto">
                  {roles.map((r) => {
                    const isChecked = createForm.roles?.includes(r.code);
                    return (
                      <label
                        key={r.code}
                        className="flex items-start gap-2 p-1.5 rounded hover:bg-white cursor-pointer transition-colors"
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            const newRoles = e.target.checked
                              ? [...(createForm.roles || []), r.code]
                              : (createForm.roles || []).filter((c) => c !== r.code);
                            setCreateForm({ ...createForm, roles: newRoles });
                          }}
                          className="mt-0.5 rounded border-gqt-neutral-300 text-gqt-blue"
                        />
                        <div className="text-[11px] leading-tight">
                          <div className="font-bold text-gqt-charcoal">{r.code}</div>
                          <div className="text-gqt-neutral-500 text-[10px]">{r.name}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-end gap-2 shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCreateModalOpen(false)}
                disabled={createMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={createMutation.isPending}
                onClick={() => {
                  setModalFormError(null);
                  createMutation.mutate(createForm);
                }}
                className="bg-gqt-navy hover:bg-gqt-navy-light text-white"
              >
                Provision Account
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Edit User Profile Modal */}
      {editingUser && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden border border-gqt-neutral-200">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="edit-modal-title" className="text-base font-bold">
                  Edit User Profile
                </h3>
              </div>
              <button
                onClick={() => setEditingUser(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal">
              {modalFormError && (
                <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{modalFormError}</span>
                </div>
              )}

              {/* Readonly Email */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-neutral-500">Email Address (Immutable)</label>
                <input
                  type="email"
                  disabled
                  value={editingUser.email}
                  className="w-full px-3 py-2 bg-gqt-neutral-100 border border-gqt-neutral-200 rounded-lg text-xs text-gqt-neutral-600 cursor-not-allowed font-mono"
                />
              </div>

              {/* First Name */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">First Name</label>
                <input
                  type="text"
                  value={editForm.first_name}
                  onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Last Name */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">Last Name</label>
                <input
                  type="text"
                  value={editForm.last_name}
                  onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Phone */}
              <div className="space-y-1">
                <label className="font-semibold text-gqt-charcoal">Phone Number</label>
                <input
                  type="tel"
                  value={editForm.phone_number}
                  onChange={(e) => setEditForm({ ...editForm, phone_number: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full px-3 py-2 border border-gqt-neutral-300 rounded-lg text-xs text-gqt-charcoal focus:ring-2 focus:ring-gqt-blue"
                />
              </div>
            </div>

            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingUser(null)}
                disabled={updateMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={updateMutation.isPending}
                onClick={() => {
                  setModalFormError(null);
                  updateMutation.mutate({ id: editingUser.id, payload: editForm });
                }}
                className="bg-gqt-navy hover:bg-gqt-navy-light text-white"
              >
                Save Profile Changes
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 3. Manage Roles Modal */}
      {roleManagingUser && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="roles-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-gqt-neutral-200 max-h-[85vh] flex flex-col">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="roles-modal-title" className="text-base font-bold">
                  Manage Roles: {roleManagingUser.full_name}
                </h3>
              </div>
              <button
                onClick={() => setRoleManagingUser(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal overflow-y-auto">
              <p className="text-gqt-neutral-600">
                Configure operational permissions for <strong className="text-gqt-navy">{roleManagingUser.email}</strong>.
                Role updates are executed atomically with strict safeguard validations.
              </p>

              {roleManagingUser.id === currentUser?.id && (
                <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-lg text-xs flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>
                    <strong>Self-Account Notice:</strong> You are modifying your own user account. The ADMIN role cannot be revoked from your own account to prevent administrative lockout.
                  </span>
                </div>
              )}

              {modalFormError && (
                <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span>{modalFormError}</span>
                </div>
              )}

              <div className="space-y-2">
                {roles.map((r) => {
                  const isChecked = selectedRoleCodes.includes(r.code);
                  return (
                    <label
                      key={r.code}
                      className={`flex items-start gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${isChecked
                        ? 'bg-blue-50/50 border-gqt-blue'
                        : 'bg-white border-gqt-neutral-200 hover:bg-gqt-neutral-50'
                        }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedRoleCodes([...selectedRoleCodes, r.code]);
                          } else {
                            setSelectedRoleCodes(selectedRoleCodes.filter((c) => c !== r.code));
                          }
                        }}
                        className="mt-1 rounded border-gqt-neutral-300 text-gqt-blue focus:ring-gqt-blue"
                      />
                      <div className="space-y-0.5">
                        <div className="font-bold text-gqt-navy flex items-center gap-2">
                          <span>{r.name}</span>
                          <span className="font-mono text-[10px] text-gqt-neutral-500 bg-gqt-neutral-100 px-1.5 py-0.5 rounded">
                            {r.code}
                          </span>
                        </div>
                        {r.description && (
                          <p className="text-gqt-neutral-500 text-[11px] leading-relaxed">
                            {r.description}
                          </p>
                        )}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-end gap-2 shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRoleManagingUser(null)}
                disabled={rolesMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={rolesMutation.isPending}
                onClick={() => {
                  setModalFormError(null);
                  rolesMutation.mutate({
                    id: roleManagingUser.id,
                    roleCodes: selectedRoleCodes,
                  });
                }}
                className="bg-gqt-navy hover:bg-gqt-navy-light text-white"
              >
                Synchronize Roles
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 4. Deactivation / Activation Confirmation Dialog */}
      {statusConfirmUser && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="status-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden border border-gqt-neutral-200">
            <div
              className={`p-4 text-white flex items-center justify-between ${statusConfirmUser.is_active ? 'bg-rose-700' : 'bg-gqt-navy'
                }`}
            >
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-white" />
                <h3 id="status-modal-title" className="text-base font-bold">
                  Confirm Account {statusConfirmUser.is_active ? 'Deactivation' : 'Re-activation'}
                </h3>
              </div>
              <button
                onClick={() => setStatusConfirmUser(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-3 text-xs text-gqt-charcoal">
              <p>
                Are you sure you want to{' '}
                <strong>{statusConfirmUser.is_active ? 'deactivate' : 'reactivate'}</strong> the
                account for <strong className="text-gqt-navy">{statusConfirmUser.email}</strong>?
              </p>

              {statusConfirmUser.is_active ? (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-lg space-y-1">
                  <div className="font-bold flex items-center gap-1 text-rose-950">
                    <XCircle className="w-4 h-4 text-rose-600" />
                    Immediate Session Revocation
                  </div>
                  <p className="text-[11px] leading-relaxed text-rose-800">
                    Deactivating this account will immediately blacklist all active JWT refresh tokens and prevent this user from signing in across all platform workspaces.
                  </p>
                </div>
              ) : (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-900 rounded-lg space-y-1">
                  <div className="font-bold flex items-center gap-1 text-emerald-950">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Authentication Restored
                  </div>
                  <p className="text-[11px] leading-relaxed text-emerald-800">
                    Re-activating this account restores the user's ability to authenticate with their existing credentials.
                  </p>
                </div>
              )}
            </div>

            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStatusConfirmUser(null)}
                disabled={statusMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant={statusConfirmUser.is_active ? 'danger' : 'primary'}
                size="sm"
                isLoading={statusMutation.isPending}
                onClick={() =>
                  statusMutation.mutate({
                    id: statusConfirmUser.id,
                    isActive: !statusConfirmUser.is_active,
                  })
                }
              >
                {statusConfirmUser.is_active ? 'Confirm Deactivation' : 'Confirm Activation'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 5. Audit History Modal */}
      {auditViewingUser && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="audit-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full overflow-hidden border border-gqt-neutral-200 max-h-[85vh] flex flex-col">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <History className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="audit-modal-title" className="text-base font-bold">
                  Security Audit Trail: {auditViewingUser.full_name} ({auditViewingUser.email})
                </h3>
              </div>
              <button
                onClick={() => setAuditViewingUser(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal overflow-y-auto">
              <div className="p-3 bg-blue-50 border border-blue-200 text-blue-900 rounded-lg text-[11px] leading-relaxed">
                Immutable, append-only security log for this user account. All passwords, authentication tokens, and secrets are strictly redacted at the storage and API boundaries.
              </div>

              {isAuditLoading ? (
                <div className="py-8">
                  <LoadingState message="Loading historical audit entries..." />
                </div>
              ) : !auditResponse?.data || auditResponse.data.length === 0 ? (
                <div className="p-6 text-center text-gqt-neutral-500 italic">
                  No security audit events recorded for this user account yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {auditResponse.data.map((log: UserAuditLog) => (
                    <div
                      key={log.id}
                      className="p-3.5 bg-gqt-neutral-50 border border-gqt-neutral-200 rounded-lg space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-gqt-navy text-xs bg-white px-2 py-0.5 rounded border border-gqt-neutral-200">
                          {log.action}
                        </span>
                        <span className="text-[11px] text-gqt-neutral-500">
                          {new Date(log.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-[11px] text-gqt-neutral-600">
                        <div>
                          <span className="text-gqt-neutral-400">Actor: </span>
                          <strong className="text-gqt-charcoal">
                            {log.actor_name} ({log.actor_email})
                          </strong>
                        </div>
                        <div>
                          <span className="text-gqt-neutral-400">IP Address: </span>
                          <span className="font-mono text-gqt-charcoal">{log.ip_address || 'Internal/CLI'}</span>
                        </div>
                        {log.correlation_id && (
                          <div className="col-span-2">
                            <span className="text-gqt-neutral-400">Correlation ID: </span>
                            <span className="font-mono text-gqt-charcoal">{log.correlation_id}</span>
                          </div>
                        )}
                      </div>

                      {log.changes && Object.keys(log.changes).length > 0 && (
                        <div className="mt-2 bg-white p-2.5 rounded border border-gqt-neutral-200">
                          <span className="font-semibold text-gqt-neutral-500 uppercase text-[10px]">
                            Metadata & Changes:
                          </span>
                          <pre className="mt-1 text-[11px] text-gqt-charcoal whitespace-pre-wrap font-mono overflow-x-auto">
                            {JSON.stringify(log.changes, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Audit Pagination */}
            {auditResponse?.meta && auditResponse.meta.total_pages > 1 && (
              <div className="p-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-between text-xs text-gqt-neutral-600 shrink-0">
                <span>
                  Page {auditResponse.meta.current_page} of {auditResponse.meta.total_pages}
                </span>
                <div className="flex items-center gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAuditPage((p) => Math.max(p - 1, 1))}
                    disabled={!auditResponse.meta.previous}
                  >
                    Previous
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAuditPage((p) => p + 1)}
                    disabled={!auditResponse.meta.next}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}

            <div className="p-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex justify-end shrink-0">
              <Button size="sm" variant="outline" onClick={() => setAuditViewingUser(null)}>
                Close Audit View
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
