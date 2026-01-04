/**
 * PWA Install Prompt Component
 * Shows a beautiful bottom sheet prompting users to install the app
 * Only appears when app is not installed and user hasn't dismissed it
 */

import React, { useState, useEffect } from 'react';
import { Download, X, Smartphone } from 'lucide-react';

const InstallPrompt = () => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [deferredPrompt, setDeferredPrompt] = useState(null);
    const [isInstalled, setIsInstalled] = useState(false);

    useEffect(() => {
        // Check if app is already installed
        const checkInstalled = () => {
            // Check for standalone mode (installed PWA)
            if (window.matchMedia('(display-mode: standalone)').matches) {
                setIsInstalled(true);
                return true;
            }
            // Check for iOS standalone
            if (window.navigator.standalone) {
                setIsInstalled(true);
                return true;
            }
            return false;
        };

        // Check if user has dismissed the prompt recently
        const checkDismissed = () => {
            const dismissed = localStorage.getItem('pwa-install-dismissed');
            if (dismissed) {
                const dismissedTime = parseInt(dismissed, 10);
                const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
                // Don't show again for 7 days after dismissal
                if (daysSinceDismissed < 7) {
                    return true;
                }
            }
            return false;
        };

        if (checkInstalled() || checkDismissed()) {
            return;
        }

        // Listen for beforeinstallprompt event
        const handleBeforeInstallPrompt = (e) => {
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            // Stash the event so it can be triggered later
            setDeferredPrompt(e);
            // Show the custom install prompt after a delay
            setTimeout(() => {
                setShowPrompt(true);
            }, 3000); // Show after 3 seconds
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

        // Listen for successful installation
        const handleAppInstalled = () => {
            setIsInstalled(true);
            setShowPrompt(false);
            setDeferredPrompt(null);
        };

        window.addEventListener('appinstalled', handleAppInstalled);

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
            window.removeEventListener('appinstalled', handleAppInstalled);
        };
    }, []);

    const handleInstallClick = async () => {
        if (!deferredPrompt) {
            return;
        }

        // Show the install prompt
        deferredPrompt.prompt();

        // Wait for the user to respond to the prompt
        const { outcome } = await deferredPrompt.userChoice;

        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
        } else {
            console.log('User dismissed the install prompt');
        }

        // Clear the deferredPrompt
        setDeferredPrompt(null);
        setShowPrompt(false);
    };

    const handleDismiss = () => {
        setShowPrompt(false);
        // Store dismissal timestamp
        localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    };

    if (!showPrompt || isInstalled) {
        return null;
    }

    return (
        <>
            {/* Backdrop */}
            <div
                className="install-prompt-backdrop"
                onClick={handleDismiss}
            />

            {/* Install Prompt Bottom Sheet */}
            <div className="install-prompt-container">
                <div className="install-prompt-content">
                    {/* Close Button */}
                    <button
                        onClick={handleDismiss}
                        className="absolute top-3 right-3 p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5" />
                    </button>

                    {/* Icon */}
                    <div className="install-prompt-icon">
                        <Smartphone className="w-10 h-10 text-gold-400" />
                    </div>

                    {/* Content */}
                    <div className="text-center mb-6">
                        <h3 className="text-xl font-bold text-white mb-2">
                            Install Realty Pro
                        </h3>
                        <p className="text-sm text-gray-400">
                            Get the full app experience with faster access and offline support.
                            Works just like a native app!
                        </p>
                    </div>

                    {/* Benefits */}
                    <div className="space-y-2 mb-6">
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <div className="w-1.5 h-1.5 rounded-full bg-gold-400" />
                            <span>Access from your home screen</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <div className="w-1.5 h-1.5 rounded-full bg-gold-400" />
                            <span>Faster loading times</span>
                        </div>
                        <div className="flex items-center gap-3 text-sm text-gray-300">
                            <div className="w-1.5 h-1.5 rounded-full bg-gold-400" />
                            <span>Works offline</span>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            onClick={handleDismiss}
                            className="flex-1 px-6 py-3 rounded-xl font-medium transition-all duration-200 border border-white/10 text-gray-400 hover:bg-white/5"
                        >
                            Maybe Later
                        </button>
                        <button
                            onClick={handleInstallClick}
                            className="flex-1 btn-gold flex items-center justify-center gap-2"
                        >
                            <Download className="w-5 h-5" />
                            Install Now
                        </button>
                    </div>
                </div>
            </div>
        </>
    );
};

export default InstallPrompt;
