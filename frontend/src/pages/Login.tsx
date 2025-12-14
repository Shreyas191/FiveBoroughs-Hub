import React, { useState } from 'react';
import { auth } from '../firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';
import { useNavigate } from 'react-router-dom';
import { LogIn, UserPlus } from 'lucide-react';

const Login: React.FC = () => {
    const [isSignUp, setIsSignUp] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            if (isSignUp) {
                await createUserWithEmailAndPassword(auth, email, password);
            } else {
                await signInWithEmailAndPassword(auth, email, password);
            }
            navigate('/');
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="min-h-[80vh] flex items-center justify-center">
            <div className="glass-panel p-8 w-full max-w-md mx-4">
                <h2 className="text-2xl font-bold mb-6 text-center">
                    {isSignUp ? 'Create Account' : 'Welcome Back'}
                </h2>

                {error && (
                    <div className="p-3 mb-4 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleAuth} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Email</label>
                        <input
                            type="email"
                            required
                            className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-1">Password</label>
                        <input
                            type="password"
                            required
                            className="w-full bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                        />
                    </div>

                    <button type="submit" className="btn-primary w-full flex justify-center items-center gap-2 mt-6">
                        {isSignUp ? <UserPlus size={18} /> : <LogIn size={18} />}
                        {isSignUp ? 'Sign Up' : 'Login'}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm">
                    <button
                        onClick={() => setIsSignUp(!isSignUp)}
                        className="text-blue-400 hover:text-blue-300 underline"
                    >
                        {isSignUp ? 'Already have an account? Login' : "Don't have an account? Sign Up"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Login;
