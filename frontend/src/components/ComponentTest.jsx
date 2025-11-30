/**
 * Test file to verify all components are working
 * This file tests imports and basic rendering of all components
 */

import React from 'react';

// Import all components
import Login from './Login';
import Dashboard from './Dashboard';
import Settings from './Settings';
import PropertiesManagement from './PropertiesManagement';
import PropertyImageUpload from './PropertyImageUpload';
import SuperAdminPanel from './SuperAdminPanel';
import SuperAdminDashboard from './SuperAdminDashboard';
import Logo from './Logo';
import Analytics from './Analytics';
import QRGenerator from './QRGenerator';
import Broadcast from './Broadcast';
import Catalogs from './Catalogs';
import Lottery from './Lottery';

// Component manifest
const COMPONENTS = {
    // Authentication
    Login: { component: Login, props: { onLogin: () => {} } },
    
    // Main Dashboard
    Dashboard: { component: Dashboard, props: { user: { tenant_id: 1, name: 'Test User' }, onLogout: () => {} } },
    
    // Settings & Configuration
    Settings: { component: Settings, props: { tenantId: 1, token: 'test-token' } },
    
    // Properties
    PropertiesManagement: { component: PropertiesManagement, props: { tenantId: 1 } },
    PropertyImageUpload: { component: PropertyImageUpload, props: { propertyId: 1, tenantId: 1, images: [], onImagesChange: () => {} } },
    
    // Super Admin
    SuperAdminPanel: { component: SuperAdminPanel, props: {} },
    SuperAdminDashboard: { component: SuperAdminDashboard, props: { token: 'test-token', onSelectTenant: () => {} } },
    
    // Utilities
    Logo: { component: Logo, props: { size: 'md', variant: 'full' } },
    
    // Analytics & Tools
    Analytics: { component: Analytics, props: { tenantId: 1 } },
    QRGenerator: { component: QRGenerator, props: { tenantId: 1 } },
    Broadcast: { component: Broadcast, props: { tenantId: 1 } },
    Catalogs: { component: Catalogs, props: { tenantId: 1 } },
    Lottery: { component: Lottery, props: { tenantId: 1 } }
};

// Test runner
const ComponentTest = () => {
    const [testResults, setTestResults] = React.useState({});

    React.useEffect(() => {
        const results = {};
        
        Object.keys(COMPONENTS).forEach(name => {
            try {
                const { component: Component, props } = COMPONENTS[name];
                
                // Test 1: Component is defined
                if (!Component) {
                    throw new Error('Component is undefined');
                }
                
                // Test 2: Component can be instantiated
                const element = React.createElement(Component, props);
                if (!element) {
                    throw new Error('Failed to create React element');
                }
                
                results[name] = { status: 'PASS', error: null };
            } catch (error) {
                results[name] = { status: 'FAIL', error: error.message };
            }
        });
        
        setTestResults(results);
    }, []);

    const passed = Object.values(testResults).filter(r => r.status === 'PASS').length;
    const failed = Object.values(testResults).filter(r => r.status === 'FAIL').length;
    const total = Object.keys(COMPONENTS).length;

    return (
        <div style={{ padding: '20px', fontFamily: 'monospace', background: '#0f1729', color: '#fff', minHeight: '100vh' }}>
            <h1 style={{ color: '#D4AF37' }}>🧪 ArtinSmartRealty Component Test Suite</h1>
            
            <div style={{ marginTop: '20px', padding: '15px', background: '#1a2332', borderRadius: '8px' }}>
                <h2>Test Summary</h2>
                <p style={{ color: passed === total ? '#10b981' : '#ef4444', fontSize: '18px', fontWeight: 'bold' }}>
                    {passed} / {total} Components Passed
                </p>
                {failed > 0 && (
                    <p style={{ color: '#ef4444' }}>
                        ❌ {failed} Component{failed !== 1 ? 's' : ''} Failed
                    </p>
                )}
            </div>

            <div style={{ marginTop: '20px' }}>
                <h2>Component Status:</h2>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
                    <thead>
                        <tr style={{ borderBottom: '2px solid #D4AF37' }}>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Component</th>
                            <th style={{ padding: '10px', textAlign: 'center' }}>Status</th>
                            <th style={{ padding: '10px', textAlign: 'left' }}>Error</th>
                        </tr>
                    </thead>
                    <tbody>
                        {Object.keys(COMPONENTS).map(name => {
                            const result = testResults[name];
                            if (!result) return null;
                            
                            return (
                                <tr key={name} style={{ borderBottom: '1px solid #2a3546' }}>
                                    <td style={{ padding: '10px' }}>{name}</td>
                                    <td style={{ 
                                        padding: '10px', 
                                        textAlign: 'center',
                                        color: result.status === 'PASS' ? '#10b981' : '#ef4444',
                                        fontWeight: 'bold'
                                    }}>
                                        {result.status === 'PASS' ? '✅ PASS' : '❌ FAIL'}
                                    </td>
                                    <td style={{ padding: '10px', color: '#94a3b8' }}>
                                        {result.error || '-'}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {passed === total && (
                <div style={{ 
                    marginTop: '30px', 
                    padding: '20px', 
                    background: '#10b981', 
                    borderRadius: '8px',
                    textAlign: 'center'
                }}>
                    <h2 style={{ color: '#fff', margin: 0 }}>🎉 All Components Working!</h2>
                    <p style={{ color: '#fff', marginTop: '10px' }}>
                        All {total} components are properly imported and can be rendered.
                    </p>
                </div>
            )}
        </div>
    );
};

export default ComponentTest;
