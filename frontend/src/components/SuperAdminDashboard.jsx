/**
 * Artin Smart Realty V2 - Super Admin Dashboard
 * Platform owner dashboard for managing all tenants
 */

import React from 'react';
import SuperAdminPanel from './SuperAdminPanel';

const SuperAdminDashboard = ({ token, onSelectTenant }) => {
    return <SuperAdminPanel onSelectTenant={onSelectTenant} />;
};

export default SuperAdminDashboard;
