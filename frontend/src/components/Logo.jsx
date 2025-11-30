/**
 * Artin Smart Realty V2 - Logo Component
 * Centralized logo management
 */

import React from 'react';
import { Building2 } from 'lucide-react';
import goldLogo from '../goldlogo.svg';

const Logo = ({ size = 'md', variant = 'full' }) => {
  const sizes = {
    sm: { icon: 24, container: 'w-10 h-10', text: 'text-lg' },
    md: { icon: 32, container: 'w-16 h-16', text: 'text-2xl' },
    lg: { icon: 40, container: 'w-20 h-20', text: 'text-3xl' },
  };

  const currentSize = sizes[size];

  // لوگوی سفارشی از پوشه src
  const customLogoPath = goldLogo;

  if (variant === 'icon') {
    return (
      <div className={`inline-flex items-center justify-center ${currentSize.container} bg-gradient-to-br from-gold-500 to-gold-600 rounded-xl`}>
        {customLogoPath ? (
          <img src={customLogoPath} alt="Artin Smart Realty" className="w-full h-full object-contain p-2" />
        ) : (
          <Building2 className="text-navy-900" size={currentSize.icon} />
        )}
      </div>
    );
  }

  if (variant === 'text') {
    return (
      <div>
        <h1 className={`${currentSize.text} font-bold text-gold-500`}>Artin Smart Realty</h1>
        <p className="text-gray-400 text-xs mt-1">Real Estate Platform v2.0</p>
      </div>
    );
  }

  // Full logo with icon and text
  return (
    <div className="flex items-center gap-3">
      <div className={`inline-flex items-center justify-center ${currentSize.container} bg-gradient-to-br from-gold-500 to-gold-600 rounded-xl flex-shrink-0`}>
        {customLogoPath ? (
          <img src={customLogoPath} alt="Artin Smart Realty" className="w-full h-full object-contain p-2" />
        ) : (
          <Building2 className="text-navy-900" size={currentSize.icon} />
        )}
      </div>
      <div>
        <h1 className={`${currentSize.text} font-bold text-gold-500`}>Artin Smart Realty</h1>
        <p className="text-gray-400 text-xs mt-1">Enterprise Platform</p>
      </div>
    </div>
  );
};

export default Logo;
