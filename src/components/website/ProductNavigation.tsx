import React, { useState, useEffect } from 'react';
import { ArrowUpRight, Smartphone, Activity } from 'lucide-react';

interface ProductNavigationProps {
  onLaunchStudio: () => void;
  activeSection?: string;
}

export const ProductNavigation: React.FC<ProductNavigationProps> = ({
  onLaunchStudio,
}) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { label: 'Overview', href: '#overview' },
    { label: 'The Challenge', href: '#problem' },
    { label: 'Approach', href: '#approach' },
    { label: 'Optical Screening', href: '#optical' },
    { label: 'Anthropometry', href: '#anthropometry' },
    { label: 'Safety Engine', href: '#safety' },
    { label: 'Frontline Field', href: '#frontline' },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'apple-glass py-3.5 shadow-[0_1px_12px_rgba(0,0,0,0.04)]'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-[1180px] mx-auto px-6 flex items-center justify-between">
        {/* Brand Wordmark */}
        <a
          href="#overview"
          className="flex items-center gap-2.5 text-[#1d1d1f] hover:opacity-80 transition-opacity"
        >
          <div className="w-5 h-5 rounded-full bg-[#1d1d1f] flex items-center justify-center text-white">
            <Activity className="w-3 h-3 stroke-[2.5]" />
          </div>
          <span className="font-semibold text-[17px] tracking-tight text-[#1d1d1f]">
            PRAHARI
          </span>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-[13px] font-normal text-[#6e6e73] hover:text-[#1d1d1f] transition-colors tracking-tight"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Primary CTA Action */}
        <div className="flex items-center gap-3">
          <button
            onClick={onLaunchStudio}
            className="apple-btn-accent text-[13px] px-4 py-2 inline-flex items-center gap-1.5 cursor-pointer shadow-sm"
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>Launch Frontline App</span>
            <ArrowUpRight className="w-3 h-3 opacity-70" />
          </button>

          {/* Mobile Menu Trigger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-[#1d1d1f] focus:outline-none"
            aria-label="Toggle menu"
          >
            <div className="w-5 h-4 flex flex-col justify-between">
              <span
                className={`h-0.5 bg-[#1d1d1f] rounded transition-transform ${
                  mobileMenuOpen ? 'rotate-45 translate-y-1.5' : ''
                }`}
              />
              <span
                className={`h-0.5 bg-[#1d1d1f] rounded transition-opacity ${
                  mobileMenuOpen ? 'opacity-0' : ''
                }`}
              />
              <span
                className={`h-0.5 bg-[#1d1d1f] rounded transition-transform ${
                  mobileMenuOpen ? '-rotate-45 -translate-y-1.5' : ''
                }`}
              />
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden apple-glass px-6 py-6 border-t border-black/[0.06] mt-3 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="text-[15px] font-medium text-[#1d1d1f] py-1"
              >
                {link.label}
              </a>
            ))}
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onLaunchStudio();
              }}
              className="apple-btn-accent text-[14px] py-3 text-center w-full mt-2 font-medium"
            >
              Launch Frontline App
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
