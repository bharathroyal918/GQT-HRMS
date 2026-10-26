import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { GraduationCap, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { studentsApi } from '@/api/studentsApi';
import { StudentRegisterPayload } from '@/types/students';
import { Button } from '@/components/common/Button';
import { Input } from '@/components/common/Input';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';

export const StudentRegistrationPage: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState<StudentRegisterPayload>({
    email: '',
    password: '',
    roll_number: '',
    first_name: '',
    last_name: '',
    college_name: 'GQT Institute of Technology',
    degree: 'B.Tech',
    department: 'Computer Science & Engineering',
    graduation_year: 2025,
    cgpa: '8.00',
    active_backlogs: 0,
    history_backlogs: 0,
    phone_number: '',
    alternate_phone: '',
  });

  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});
  const [isSuccess, setIsSuccess] = useState(false);

  const registerMutation = useMutation({
    mutationFn: (data: StudentRegisterPayload) => studentsApi.registerStudent(data),
    onSuccess: () => {
      setIsSuccess(true);
      setServerErrors({});
    },
    onError: (err: any) => {
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        const errors: Record<string, string> = {};
        for (const [key, val] of Object.entries(data)) {
          errors[key] = Array.isArray(val) ? val.join(' ') : String(val);
        }
        setServerErrors(errors);
      } else {
        setServerErrors({ general: 'Registration failed. Please check inputs and try again.' });
      }
    },
  });

  const handleChange = (field: keyof StudentRegisterPayload, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (serverErrors[field]) {
      setServerErrors(prev => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    registerMutation.mutate(formData);
  };

  if (isSuccess) {
    return (
      <div className="min-h-screen bg-gqt-neutral-50 flex items-center justify-center p-4">
        <Card className="max-w-md w-full text-center p-6 space-y-4">
          <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <CardTitle className="text-xl text-gqt-navy">Student Account Created!</CardTitle>
          <CardDescription>
            Your student profile has been registered with roll number{' '}
            <span className="font-semibold text-gqt-navy">{formData.roll_number.toUpperCase()}</span>. You can now log in to the recruitment portal and upload your placement resume.
          </CardDescription>
          <div className="pt-4">
            <Button onClick={() => navigate('/login')} className="w-full">
              Proceed to Sign In
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gqt-neutral-50 py-12 px-4 sm:px-6 lg:px-8 flex flex-col justify-center">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="flex justify-center mb-3">
          <div className="w-12 h-12 bg-gqt-navy text-white rounded-xl flex items-center justify-center shadow-md">
            <GraduationCap className="w-6 h-6" />
          </div>
        </div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-gqt-navy">
          GQT Student Registration & Onboarding
        </h2>
        <p className="mt-1 text-center text-sm text-gqt-neutral-500">
          Workflow Step 11: Register your academic credentials for institutional campus recruitment drives.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Candidate Academic Identity</CardTitle>
            <CardDescription>
              Roll numbers and institutional email addresses are uniquely validated against GQT enrollment records.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {serverErrors.general && (
              <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{serverErrors.general}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="First Name"
                  required
                  value={formData.first_name}
                  onChange={e => handleChange('first_name', e.target.value)}
                  error={serverErrors.first_name}
                  placeholder="e.g. Rahul"
                />
                <Input
                  label="Last Name"
                  required
                  value={formData.last_name}
                  onChange={e => handleChange('last_name', e.target.value)}
                  error={serverErrors.last_name}
                  placeholder="e.g. Sharma"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Institutional Email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={e => handleChange('email', e.target.value)}
                  error={serverErrors.email || serverErrors.institutional_email}
                  placeholder="e.g. rahul.sharma@gqt.edu"
                />
                <Input
                  label="Password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={e => handleChange('password', e.target.value)}
                  error={serverErrors.password}
                  placeholder="Minimum 8 characters"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="University Roll / Reg Number"
                  required
                  value={formData.roll_number}
                  onChange={e => handleChange('roll_number', e.target.value)}
                  error={serverErrors.roll_number}
                  placeholder="e.g. 1GQT21CS042"
                />
                <Input
                  label="Primary Phone Number"
                  value={formData.phone_number}
                  onChange={e => handleChange('phone_number', e.target.value)}
                  error={serverErrors.phone_number}
                  placeholder="e.g. +91 98765 43210"
                />
              </div>

              <Input
                label="College / Institute Name"
                required
                value={formData.college_name}
                onChange={e => handleChange('college_name', e.target.value)}
                error={serverErrors.college_name}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                    Degree Program <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={formData.degree}
                    onChange={e => handleChange('degree', e.target.value)}
                    className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  >
                    <option value="B.Tech">B.Tech (Bachelor of Technology)</option>
                    <option value="B.E.">B.E. (Bachelor of Engineering)</option>
                    <option value="M.Tech">M.Tech (Master of Technology)</option>
                    <option value="MCA">MCA (Master of Computer Applications)</option>
                    <option value="BCA">BCA (Bachelor of Computer Applications)</option>
                    <option value="B.Sc">B.Sc Computer Science</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                    Department / Branch <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={formData.department}
                    onChange={e => handleChange('department', e.target.value)}
                    className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  >
                    <option value="Computer Science & Engineering">Computer Science & Engineering</option>
                    <option value="Information Science & Engineering">Information Science & Engineering</option>
                    <option value="Electronics & Communication">Electronics & Communication</option>
                    <option value="Electrical & Electronics">Electrical & Electronics</option>
                    <option value="Mechanical Engineering">Mechanical Engineering</option>
                    <option value="Civil Engineering">Civil Engineering</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Input
                  label="Passing Batch (Year)"
                  type="number"
                  required
                  value={formData.graduation_year}
                  onChange={e => handleChange('graduation_year', parseInt(e.target.value) || 2025)}
                  error={serverErrors.graduation_year}
                />
                <Input
                  label="Current CGPA (10.0 scale)"
                  required
                  value={formData.cgpa}
                  onChange={e => handleChange('cgpa', e.target.value)}
                  error={serverErrors.cgpa}
                  placeholder="e.g. 8.25"
                />
                <Input
                  label="Active Backlogs Count"
                  type="number"
                  value={formData.active_backlogs}
                  onChange={e => handleChange('active_backlogs', parseInt(e.target.value) || 0)}
                  error={serverErrors.active_backlogs}
                />
              </div>

              <div className="pt-3">
                <Button
                  type="submit"
                  disabled={registerMutation.isPending}
                  className="w-full"
                >
                  {registerMutation.isPending ? 'Registering Account...' : 'Complete Student Registration'}
                </Button>
              </div>

              <div className="text-center pt-2">
                <Link to="/login" className="text-sm font-medium text-gqt-blue hover:underline">
                  Already registered? Sign in to your account
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
