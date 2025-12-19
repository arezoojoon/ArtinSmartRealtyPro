import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';

function SuperadminPanel() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [newTenantInfo, setNewTenantInfo] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [formData, setFormData] = useState({
    company_name: '',
    subdomain: '',
    admin_username: '',
    admin_email: '',
    admin_password: '',
    admin_full_name: '',
    subscription_plan: 'basic'
  });

  useEffect(() => {
    // Use user from AuthContext instead of localStorage
    if (user?.role !== 'superadmin') {
      toast.error('⛔ Access Denied - Superadmin Only');
      navigate('/dashboard');
      return;
    }
    fetchTenants();
  }, [user]);

  const fetchTenants = async () => {
    try {
      const response = await api.get('/api/superadmin/tenants');
      setTenants(response.data.tenants || []);
    } catch (error) {
      console.error('❌ خطا در دریافت لیست tenants:', error);
      if (error.response?.status === 403) {
        toast.error('⛔ Unauthorized - You are not a superadmin');
        navigate('/dashboard');
      } else {
        toast.error('❌ Failed to fetch tenants list');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    
    // Validation - Empty fields
    if (!formData.company_name || !formData.subdomain || !formData.admin_username || 
        !formData.admin_email || !formData.admin_password) {
      toast.error('❌ Please fill in all required fields');
      return;
    }

    // Company name validation (حداقل 2 کاراکتر)
    if (formData.company_name.trim().length < 2) {
      toast.error('❌ Company name must be at least 2 characters');
      return;
    }

    // Subdomain validation (حداقل 3 کاراکتر، فقط حروف کوچک، اعداد و dash)
    if (formData.subdomain.length < 3) {
      toast.error('❌ Subdomain must be at least 3 characters');
      return;
    }
    if (!/^[a-z0-9-]+$/.test(formData.subdomain)) {
      toast.error('❌ Subdomain must contain only lowercase letters, numbers and dashes');
      return;
    }

    // Username validation (حداقل 3 کاراکتر، فقط حروف، اعداد، نقطه، خط تیره، زیرخط)
    if (formData.admin_username.length < 3) {
      toast.error('❌ Username must be at least 3 characters');
      return;
    }
    if (!/^[a-zA-Z0-9_.-]+$/.test(formData.admin_username)) {
      toast.error('❌ Username can only contain letters, numbers, dots, dashes and underscores');
      return;
    }

    // Email validation (basic check)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.admin_email)) {
      toast.error('❌ Invalid email format');
      return;
    }

    // Password validation (حداقل 8 کاراکتر)
    if (formData.admin_password.length < 8) {
      toast.error('❌ Password must be at least 8 characters');
      return;
    }

    // Subscription plan validation
    const validPlans = ['basic', 'pro', 'enterprise'];
    if (!validPlans.includes(formData.subscription_plan)) {
      toast.error('❌ Subscription plan must be one of: basic, pro, enterprise');
      return;
    }

    try {
      console.log('🔄 ارسال درخواست ایجاد tenant:', formData);
      const response = await api.post('/api/superadmin/tenants', formData);
      console.log('✅ پاسخ سرور:', response.data);
      
      // ذخیره اطلاعات لاگین برای نمایش
      setNewTenantInfo({
        company_name: formData.company_name,
        subdomain: formData.subdomain,
        admin_username: formData.admin_username,
        admin_password: formData.admin_password,
        admin_email: formData.admin_email
      });
      
      toast.success('✅ New tenant created successfully');
      setShowCreateModal(false);
      setShowSuccessModal(true);
      
      // Clear form
      setFormData({
        company_name: '',
        subdomain: '',
        admin_username: '',
        admin_email: '',
        admin_password: '',
        admin_full_name: '',
        subscription_plan: 'basic'
      });
      fetchTenants();
    } catch (error) {
      console.error('❌ خطا در ایجاد tenant:', error);
      console.error('❌ جزئیات خطا:', error.response?.data);
      
      // نمایش خطای دقیق از سرور
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Pydantic validation errors
          const errorMessages = error.response.data.detail.map(err => {
            const field = err.loc?.[1] || 'unknown';
            const message = err.msg || 'validation error';
            return `${field}: ${message}`;
          }).join('\n');
          toast.error(`❌ Validation error:\n${errorMessages}`);
        } else {
          toast.error(`❌ ${error.response.data.detail}`);
        }
      } else {
        toast.error('❌ Failed to create tenant');
      }
    }
  };

  const handleToggleTenant = async (tenantId, currentStatus) => {
    setSelectedTenant({ id: tenantId, isActive: currentStatus })
    setShowConfirmModal(true)
  }

  const confirmToggleTenant = async () => {
    try {
      await api.patch(`/api/superadmin/tenants/${selectedTenant.id}/toggle`, {});
      
      const newStatus = !selectedTenant.isActive;
      toast.success(`✅ Tenant ${newStatus ? 'activated' : 'deactivated'}`);
      setShowConfirmModal(false)
      setSelectedTenant(null)
      fetchTenants();
    } catch (error) {
      console.error('❌ خطا در تغییر وضعیت tenant:', error);
      toast.error('❌ Failed to change tenant status');
    }
  };

  const handleResetPassword = (tenant) => {
    setSelectedTenant(tenant);
    setNewPassword('');
    setShowResetPasswordModal(true);
  };

  const confirmResetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error('❌ Password must be at least 6 characters');
      return;
    }

    try {
      await api.post(`/api/superadmin/tenants/${selectedTenant.id}/reset-password`, {
        new_password: newPassword
      });
      
      toast.success(`✅ Password changed for ${selectedTenant.company_name} admin`);
      setShowResetPasswordModal(false);
      setSelectedTenant(null);
      setNewPassword('');
    } catch (error) {
      console.error('❌ خطا در تغییر رمز عبور:', error);
      toast.error(error.response?.data?.detail || '❌ Failed to change password');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-2xl">⏳ در حال بارگذاری...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">🔐 Superadmin Panel</h1>
            <p className="text-purple-200">مدیریت تمام Tenants پلتفرم</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/superadmin/dashboard')}
              className="px-6 py-3 bg-gradient-to-r from-amber-500 to-amber-600 text-white rounded-xl hover:scale-105 transition-transform shadow-lg flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              👁️ View All Tenants
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:scale-105 transition-transform shadow-lg"
            >
              ➕ ایجاد Tenant جدید
            </button>
          </div>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="max-w-7xl mx-auto bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-purple-600/30">
            <tr>
              <th className="px-6 py-4 text-right text-white font-semibold">ID</th>
              <th className="px-6 py-4 text-right text-white font-semibold">نام شرکت</th>
              <th className="px-6 py-4 text-right text-white font-semibold">Subdomain</th>
              <th className="px-6 py-4 text-right text-white font-semibold">پلن اشتراک</th>
              <th className="px-6 py-4 text-right text-white font-semibold">وضعیت</th>
              <th className="px-6 py-4 text-right text-white font-semibold">تاریخ ثبت</th>
              <th className="px-6 py-4 text-center text-white font-semibold">عملیات</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => (
              <tr key={tenant.id} className="border-b border-purple-400/20 hover:bg-white/5 transition">
                <td className="px-6 py-4 text-white">#{tenant.id}</td>
                <td className="px-6 py-4 text-white font-semibold">{tenant.company_name}</td>
                <td className="px-6 py-4">
                  <span className="px-3 py-1 bg-purple-500/30 text-purple-200 rounded-lg text-sm">
                    {tenant.subdomain || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-lg text-sm ${
                    tenant.subscription_plan === 'premium' ? 'bg-yellow-500/30 text-yellow-200' :
                    tenant.subscription_plan === 'pro' ? 'bg-blue-500/30 text-blue-200' :
                    'bg-gray-500/30 text-gray-200'
                  }`}>
                    {tenant.subscription_plan}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${
                    tenant.is_active ? 'bg-green-500/30 text-green-200' : 'bg-red-500/30 text-red-200'
                  }`}>
                    {tenant.is_active ? '✅ فعال' : '❌ غیرفعال'}
                  </span>
                </td>
                <td className="px-6 py-4 text-white text-sm">
                  {new Date(tenant.created_at).toLocaleDateString('fa-IR')}
                </td>
                <td className="px-6 py-4 text-center">
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => handleToggleTenant(tenant.id, tenant.is_active)}
                      className={`px-4 py-2 rounded-lg transition-all ${
                        tenant.is_active
                          ? 'bg-red-500/30 hover:bg-red-500/50 text-red-200'
                          : 'bg-green-500/30 hover:bg-green-500/50 text-green-200'
                      }`}
                    >
                      {tenant.is_active ? '🚫 غیرفعال' : '✅ فعال'}
                    </button>
                    <button
                      onClick={() => handleResetPassword(tenant)}
                      className="px-4 py-2 rounded-lg bg-yellow-500/30 hover:bg-yellow-500/50 text-yellow-200 transition-all"
                      title="تغییر رمز عبور ادمین"
                    >
                      🔑 Reset Password
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {tenants.length === 0 && (
          <div className="text-center py-12 text-purple-200">
            📭 هیچ Tenant ای وجود ندارد
          </div>
        )}
      </div>

      {/* Create Tenant Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-purple-900 to-pink-900 p-8 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-white">➕ ایجاد Tenant جدید</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-white/70 hover:text-white text-3xl"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateTenant} className="space-y-4">
              {/* Company Name */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">🏢 نام شرکت *</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                  placeholder="مثال: غرفه نمایشگاهی XYZ"
                  required
                />
              </div>

              {/* Subdomain */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">🌐 Subdomain *</label>
                <div className="flex items-center">
                  <input
                    type="text"
                    value={formData.subdomain}
                    onChange={(e) => setFormData({ ...formData, subdomain: e.target.value.toLowerCase() })}
                    className="flex-1 px-4 py-3 bg-white/10 border border-purple-400/30 rounded-l-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                    placeholder="booth1"
                    pattern="[a-z0-9-]+"
                    required
                  />
                  <span className="px-4 py-3 bg-purple-600/50 border border-purple-400/30 rounded-r-xl text-purple-200">
                    .expo.artinsmartagent.com
                  </span>
                </div>
                <p className="text-purple-300/70 text-sm mt-1">⚠️ فقط حروف کوچک، اعداد و dash</p>
              </div>

              {/* Admin Username */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">👤 نام کاربری Admin *</label>
                <input
                  type="text"
                  value={formData.admin_username}
                  onChange={(e) => setFormData({ ...formData, admin_username: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                  placeholder="admin_booth1"
                  required
                />
              </div>

              {/* Admin Email */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">📧 ایمیل Admin *</label>
                <input
                  type="email"
                  value={formData.admin_email}
                  onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                  placeholder="admin@company.com"
                  required
                />
              </div>

              {/* Admin Password */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">🔒 رمز عبور Admin *</label>
                <input
                  type="password"
                  value={formData.admin_password}
                  onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                  placeholder="حداقل 8 کاراکتر"
                  minLength={8}
                  required
                />
              </div>

              {/* Admin Full Name */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">📝 نام کامل Admin</label>
                <input
                  type="text"
                  value={formData.admin_full_name}
                  onChange={(e) => setFormData({ ...formData, admin_full_name: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white placeholder-purple-300/50 focus:outline-none focus:border-purple-400"
                  placeholder="علی احمدی"
                />
              </div>

              {/* Subscription Plan */}
              <div>
                <label className="block text-purple-200 mb-2 font-semibold">💳 پلن اشتراک</label>
                <select
                  value={formData.subscription_plan}
                  onChange={(e) => setFormData({ ...formData, subscription_plan: e.target.value })}
                  className="w-full px-4 py-3 bg-white/10 border border-purple-400/30 rounded-xl text-white focus:outline-none focus:border-purple-400"
                >
                  <option value="basic" className="bg-purple-900">Basic - پایه</option>
                  <option value="pro" className="bg-purple-900">Pro - حرفه‌ای</option>
                  <option value="premium" className="bg-purple-900">Premium - ویژه</option>
                </select>
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl hover:scale-105 transition-transform font-bold shadow-lg"
                >
                  ✅ ایجاد Tenant
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 px-6 py-3 bg-red-600/30 text-white rounded-xl hover:bg-red-600/50 transition font-bold"
                >
                  ❌ انصراف
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && selectedTenant && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-purple-900 to-pink-900 p-8 rounded-2xl shadow-2xl max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white mb-4">⚠️ تأیید تغییر وضعیت</h2>
            <p className="text-purple-200 mb-6">
              آیا مطمئن هستید که می‌خواهید این Tenant را 
              <strong className="text-white">
                {selectedTenant.isActive ? ' غیرفعال ' : ' فعال '}
              </strong>
              کنید؟
            </p>
            <div className="flex gap-4">
              <button
                onClick={confirmToggleTenant}
                className="flex-1 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl hover:scale-105 transition-transform font-bold"
              >
                ✅ بله، تأیید می‌کنم
              </button>
              <button
                onClick={() => {
                  setShowConfirmModal(false)
                  setSelectedTenant(null)
                }}
                className="flex-1 px-6 py-3 bg-red-600/30 text-white rounded-xl hover:bg-red-600/50 transition font-bold"
              >
                ❌ انصراف
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Modal - نمایش اطلاعات لاگین */}
      {showSuccessModal && newTenantInfo && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-green-900 to-emerald-900 p-8 rounded-2xl shadow-2xl max-w-2xl w-full mx-4">
            <h2 className="text-3xl font-bold text-white mb-6 text-center">
              🎉 Tenant با موفقیت ایجاد شد!
            </h2>
            
            <div className="bg-black/30 rounded-xl p-6 mb-6 space-y-4">
              <div className="text-center mb-4">
                <p className="text-green-200 text-lg">اطلاعات لاگین مدیر:</p>
              </div>
              
              <div className="grid gap-3">
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-green-300 text-sm mb-1">🏢 نام شرکت:</p>
                  <p className="text-white font-bold text-lg">{newTenantInfo.company_name}</p>
                </div>
                
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-green-300 text-sm mb-1">🌐 Subdomain:</p>
                  <p className="text-white font-bold text-lg">{newTenantInfo.subdomain}</p>
                </div>
                
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-green-300 text-sm mb-1">👤 نام کاربری:</p>
                  <div className="flex items-center justify-between">
                    <p className="text-white font-bold text-lg">{newTenantInfo.admin_username}</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(newTenantInfo.admin_username);
                        toast.success('✅ Copied!');
                      }}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-sm"
                    >
                      📋 Copy
                    </button>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-green-300 text-sm mb-1">🔑 Password:</p>
                  <div className="flex items-center justify-between">
                    <p className="text-white font-bold text-lg">{newTenantInfo.admin_password}</p>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(newTenantInfo.admin_password);
                        toast.success('✅ Copied!');
                      }}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded-lg text-sm"
                    >
                      📋 Copy
                    </button>
                  </div>
                </div>
                
                <div className="bg-white/10 rounded-lg p-3">
                  <p className="text-green-300 text-sm mb-1">📧 ایمیل:</p>
                  <p className="text-white font-bold">{newTenantInfo.admin_email}</p>
                </div>
              </div>
              
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4 mt-4">
                <p className="text-yellow-200 text-sm">
                  ⚠️ این اطلاعات را در جای امنی ذخیره کنید. برای امنیت بیشتر، بعد از اولین ورود رمز عبور را تغییر دهید.
                </p>
              </div>
            </div>
            
            <div className="flex gap-4">
              <button
                onClick={() => {
                  const loginInfo = `Company: ${newTenantInfo.company_name}\nSubdomain: ${newTenantInfo.subdomain}\nUsername: ${newTenantInfo.admin_username}\nPassword: ${newTenantInfo.admin_password}\nEmail: ${newTenantInfo.admin_email}`;
                  navigator.clipboard.writeText(loginInfo);
                  toast.success('✅ All credentials copied!');
                }}
                className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition font-bold"
              >
                📋 Copy All Info
              </button>
              <button
                onClick={() => {
                  setShowSuccessModal(false);
                  setNewTenantInfo(null);
                }}
                className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl transition font-bold"
              >
                ✅ متوجه شدم
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Reset Password Modal */}
      {showResetPasswordModal && selectedTenant && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-yellow-900 to-orange-900 p-8 rounded-2xl shadow-2xl max-w-md w-full mx-4">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-yellow-500/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">🔑</span>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">تغییر رمز عبور</h2>
              <p className="text-yellow-200">
                رمز عبور ادمین <span className="font-bold">{selectedTenant.company_name}</span>
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  رمز عبور جدید (حداقل 6 کاراکتر)
                </label>
                <input
                  type="text"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="رمز عبور جدید را وارد کنید"
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:border-yellow-500"
                  autoFocus
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowResetPasswordModal(false);
                    setSelectedTenant(null);
                    setNewPassword('');
                  }}
                  className="flex-1 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl transition"
                >
                  ❌ انصراف
                </button>
                <button
                  onClick={confirmResetPassword}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700 text-white rounded-xl transition shadow-lg"
                >
                  ✅ تایید تغییر
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SuperadminPanel
