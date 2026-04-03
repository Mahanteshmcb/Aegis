import { useState } from 'react';
import { resetPasswordAPI } from '../utils/api';

export default function ResetPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');
    try {
      const data = await resetPasswordAPI(email);
      if (data?.message) {
        setMessage(data.message);
      } else {
        setMessage('If this email exists, a reset link has been sent.');
      }
    } catch (err) {
      setError(err.message || 'Reset failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-transparent flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <h2 className="text-3xl font-extrabold tracking-tight text-white">Reset your passphrase</h2>
        <p className="mt-2 text-sm text-aegis-muted">Request a secure password reset for your operator account.</p>
      </div>
      <div className="sm:mx-auto sm:w-full sm:max-w-md relative z-10">
        <div className="glass-card glow-border py-8 px-6 sm:px-10 sm:rounded-[32px]">
          <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-1 font-medium">Email</label>
          <input
            type="email"
            className="w-full border rounded px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        {message && <div className="text-green-600 text-sm">{message}</div>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded font-semibold hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Sending...' : 'Send Reset Link'}
        </button>
          </form>
          <div className="mt-6 text-center text-sm text-aegis-muted">
            If your address exists, reset instructions will be issued securely.
          </div>
          <div className="mt-4 text-sm text-center">
            <a href="/login" className="text-aegis-primary hover:text-violet-300 transition-colors">Back to Login</a>
          </div>
        </div>
      </div>
    </div>
  );
}
