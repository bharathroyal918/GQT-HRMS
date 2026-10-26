import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { apiClient } from '../../lib/apiClient';
import { GQTLogo } from '../../components/brand/GQTLogo';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-react';

const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid work email address').toLowerCase().trim(),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const ForgotPasswordPage: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    try {
      setServerError(null);
      await apiClient.post('/auth/password/reset/request/', data);
      setSubmitted(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to dispatch reset email.';
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
          Reset Your Password
        </h1>
        <p className="mt-1 text-sm text-gqt-neutral-600">
          Enter your registered work email to receive password reset instructions.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm rounded-xl border border-gqt-neutral-200">
          {submitted ? (
            <div className="text-center py-4">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
              </div>
              <h2 className="text-lg font-semibold text-gqt-navy">Instructions Dispatched</h2>
              <p className="mt-2 text-sm text-gqt-neutral-600 leading-relaxed">
                If an account with that email address is active, you will receive an email containing a secure, short-lived reset link.
              </p>
              <div className="mt-6">
                <Link to="/login">
                  <Button variant="outline" className="w-full justify-center">
                    Return to Sign In
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
              {serverError && (
                <div role="alert" className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">
                  {serverError}
                </div>
              )}

              <Input
                label="Registered Work Email"
                type="email"
                autoComplete="email"
                placeholder="name@gqt.local"
                leftIcon={<Mail className="w-4 h-4 text-gqt-neutral-400" />}
                error={errors.email?.message}
                {...register('email')}
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full justify-center"
                isLoading={isSubmitting}
              >
                Send Reset Link
              </Button>

              <div className="text-center pt-2">
                <Link
                  to="/login"
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-gqt-neutral-600 hover:text-gqt-navy transition-colors"
                >
                  <ArrowLeft className="w-3.5 h-3.5" /> Back to Sign In
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
