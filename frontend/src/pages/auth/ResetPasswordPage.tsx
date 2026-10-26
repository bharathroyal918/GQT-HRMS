import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useSearchParams } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { GQTLogo } from '../../components/brand/GQTLogo';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Lock, CheckCircle2, AlertCircle } from 'lucide-react';

const resetPasswordSchema = z
  .object({
    new_password: z.string().min(10, 'Password must be at least 10 characters long'),
    new_password_confirm: z.string().min(10, 'Confirmation password must be at least 10 characters long'),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    message: 'Passwords do not match',
    path: ['new_password_confirm'],
  });

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid') || '';
  const token = searchParams.get('token') || '';

  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      new_password: '',
      new_password_confirm: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!uid || !token) {
      setServerError('Reset token or user identification is missing from the URL.');
      return;
    }

    try {
      setServerError(null);
      await apiClient.post('/auth/password/reset/confirm/', {
        uidb64: uid,
        token: token,
        new_password: data.new_password,
        new_password_confirm: data.new_password_confirm,
      });
      setSubmitted(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid or expired password reset link.';
      setServerError(msg);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gqt-neutral-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <GQTLogo variant="official" size="md" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-gqt-navy">
          Create New Password
        </h1>
        <p className="mt-1 text-sm text-gqt-neutral-600">
          Enter a new, strong password for your GQT HRMS account.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm rounded-xl border border-gqt-neutral-200">
          {submitted ? (
            <div className="text-center py-4">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <h2 className="text-lg font-semibold text-gqt-navy">Password Reset Successfully</h2>
              <p className="mt-2 text-sm text-gqt-neutral-600">
                Your credentials have been securely updated. You can now log into your workspace with your new password.
              </p>
              <div className="mt-6">
                <Link to="/login">
                  <Button variant="primary" className="w-full justify-center">
                    Proceed to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
              {serverError && (
                <div role="alert" className="p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3 text-sm text-red-800">
                  <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">Reset Failed</p>
                    <p className="text-red-700 mt-0.5">{serverError}</p>
                  </div>
                </div>
              )}

              <Input
                label="New Password"
                type="password"
                autoComplete="new-password"
                placeholder="Minimum 10 characters"
                leftIcon={<Lock className="w-4 h-4 text-gqt-neutral-400" />}
                error={errors.new_password?.message}
                {...register('new_password')}
              />

              <Input
                label="Confirm New Password"
                type="password"
                autoComplete="new-password"
                placeholder="Re-enter password"
                leftIcon={<Lock className="w-4 h-4 text-gqt-neutral-400" />}
                error={errors.new_password_confirm?.message}
                {...register('new_password_confirm')}
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full justify-center"
                isLoading={isSubmitting}
              >
                Set New Password
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
