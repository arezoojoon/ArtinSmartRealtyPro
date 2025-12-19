import { toast as reactToast } from 'react-toastify'
import { CheckCircle, XCircle, AlertCircle, Info, Loader } from 'lucide-react'

// Custom toast with icons
const CustomToast = ({ icon: Icon, message, type }) => (
  <div className="flex items-center gap-3">
    <Icon className={`w-5 h-5 flex-shrink-0 ${
      type === 'success' ? 'text-green-400' :
      type === 'error' ? 'text-red-400' :
      type === 'warning' ? 'text-yellow-400' :
      type === 'info' ? 'text-blue-400' :
      'text-white'
    }`} />
    <span className="text-white">{message}</span>
  </div>
)

export const toast = {
  success: (message, options = {}) => {
    reactToast.success(
      <CustomToast icon={CheckCircle} message={message} type="success" />,
      {
        ...options,
        className: 'bg-navy-800 border border-green-500/30',
        progressClassName: 'bg-green-500'
      }
    )
  },

  error: (message, options = {}) => {
    reactToast.error(
      <CustomToast icon={XCircle} message={message} type="error" />,
      {
        ...options,
        className: 'bg-navy-800 border border-red-500/30',
        progressClassName: 'bg-red-500',
        autoClose: 5000 // Longer for errors
      }
    )
  },

  warning: (message, options = {}) => {
    reactToast.warning(
      <CustomToast icon={AlertCircle} message={message} type="warning" />,
      {
        ...options,
        className: 'bg-navy-800 border border-yellow-500/30',
        progressClassName: 'bg-yellow-500'
      }
    )
  },

  info: (message, options = {}) => {
    reactToast.info(
      <CustomToast icon={Info} message={message} type="info" />,
      {
        ...options,
        className: 'bg-navy-800 border border-blue-500/30',
        progressClassName: 'bg-blue-500'
      }
    )
  },

  loading: (message, options = {}) => {
    return reactToast.loading(
      <CustomToast icon={Loader} message={message} type="loading" />,
      {
        ...options,
        className: 'bg-navy-800 border border-white/10',
        progressClassName: 'bg-gold-500'
      }
    )
  },

  update: (toastId, { message, type = 'success', ...options }) => {
    const icons = {
      success: CheckCircle,
      error: XCircle,
      warning: AlertCircle,
      info: Info
    }

    reactToast.update(toastId, {
      render: <CustomToast icon={icons[type]} message={message} type={type} />,
      type: type,
      isLoading: false,
      autoClose: 3000,
      className: `bg-navy-800 border border-${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'yellow' : 'blue'}-500/30`,
      ...options
    })
  },

  dismiss: (toastId) => {
    reactToast.dismiss(toastId)
  },

  promise: async (promise, { loading, success, error }) => {
    const toastId = toast.loading(loading)

    try {
      const result = await promise
      toast.update(toastId, { message: success, type: 'success' })
      return result
    } catch (err) {
      toast.update(toastId, { message: error || err.message, type: 'error' })
      throw err
    }
  }
}
