import React from 'react';
import { NavLink } from 'react-router-dom';
import { Train, LayoutDashboard, Map as MapIcon, Accessibility, LogIn, Globe, Navigation } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const Navbar: React.FC = () => {
    const { t, i18n } = useTranslation();

    const toggleLang = () => {
        i18n.changeLanguage(i18n.language === 'en' ? 'es' : 'en');
    };

    return (
        <nav className="sticky top-0 z-50 glass-nav w-full">
            <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">

                {/* Logo Section */}
                <NavLink to="/" className="flex items-center gap-3 group">
                    <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-900/20 group-hover:scale-105 transition-transform">
                        <Train className="text-white" size={24} />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-[var(--text-main)]">
                        NYC<span className="text-blue-500">Transit</span>
                    </span>
                </NavLink>

                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center bg-[var(--bg-card)] rounded-full px-2 py-1 border border-[var(--border-subtle)]">
                    <NavItem to="/" icon={<LayoutDashboard size={18} />} label={t('Dashboard')} />
                    <NavItem to="/map" icon={<MapIcon size={18} />} label={t('Map')} />
                    <NavItem to="/tracker" icon={<Navigation size={18} />} label="Live Tracker" />
                    <NavItem to="/accessibility" icon={<Accessibility size={18} />} label="Access" />
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={toggleLang}
                        className="p-2 rounded-full hover:bg-[var(--bg-card-hover)] text-[var(--text-scnd)] hover:text-[var(--text-main)] transition-colors border border-transparent hover:border-[var(--border-subtle)]"
                        title={i18n.language === 'en' ? "Switch to Spanish" : "Cambiar a Inglés"}
                    >
                        <Globe size={20} />
                    </button>

                    <NavLink
                        to="/login"
                        className="flex items-center gap-2 bg-[var(--bg-card)] hover:bg-[var(--bg-card-hover)] border border-[var(--border-subtle)] px-4 py-2 rounded-lg text-sm font-medium transition-all hover:border-[var(--border-highlight)]"
                    >
                        <LogIn size={16} />
                        <span className="hidden sm:inline">{t('Login')}</span>
                    </NavLink>
                </div>
            </div>
        </nav>
    );
};

const NavItem: React.FC<{ to: string, icon: React.ReactNode, label: string }> = ({ to, icon, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) => `
            flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all
            ${isActive
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-[var(--text-scnd)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-hover)]'
            }
        `}
    >
        {icon}
        <span>{label}</span>
    </NavLink>
);

export default Navbar;
