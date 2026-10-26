import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { GQTLogo } from '../../components/brand/GQTLogo';
import { Button } from '../../components/common/Button';
import { Input } from '../../components/common/Input';
import { Eye, EyeOff, Lock, Mail, AlertCircle } from 'lucide-react';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address').toLowerCase().trim(),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      setServerError(null);
      await login(data);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Invalid credentials. Please try again.';
      setServerError(msg);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-gqt-neutral-50 selection:bg-gqt-blue selection:text-white">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-block mb-6">
          <GQTLogo variant="official" size="md" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-gqt-navy">
          Sign In to Your Workspace
        </h1>
        <p className="mt-1 text-sm text-gqt-neutral-600">
          Enter your institutional credentials to access the Recruitment CRM.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 sm:px-10 shadow-sm rounded-xl border border-gqt-neutral-200">
          {serverError && (
            <div
              role="alert"
              className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 flex items-start gap-3 text-sm text-red-800"
            >
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Authentication Failed</p>
                <p className="text-red-700 mt-0.5">{serverError}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5" noValidate>
            <div>
              <Input
                label="Work Email Address"
                type="email"
                autoComplete="email"
                placeholder="name@gqt.local"
                leftIcon={<Mail className="w-4 h-4 text-gqt-neutral-400" />}
                error={errors.email?.message}
                {...register('email')}
              />
            </div>

            <div>
              <Input
                label="Password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="••••••••••••"
                leftIcon={<Lock className="w-4 h-4 text-gqt-neutral-400" />}
                rightElement={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="text-gqt-neutral-400 hover:text-gqt-charcoal transition-colors p-1"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                error={errors.password?.message}
                {...register('password')}
              />
            </div>

            <div className="flex items-center justify-between text-xs">
              <span className="text-gqt-neutral-500">HttpOnly session protection</span>
              <Link
                to="/auth/forgot-password"
                className="font-medium text-gqt-blue hover:text-gqt-blue-dark transition-colors"
              >
                Forgot password?
              </Link>
            </div>

            <div>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full justify-center"
                isLoading={isSubmitting}
              >
                Sign In
              </Button>
            </div>
          </form>

          <div className="mt-6 pt-6 border-t border-gqt-neutral-100 text-center">
            <p className="text-xs text-gqt-neutral-500">
              Need account access? Contact your GQT Placement Administrator.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
