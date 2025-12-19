import { useState } from 'react';
import { Copy, Download, Share2, QrCode, CheckCircle, AlertCircle } from 'lucide-react';

export default function WhatsAppDeepLinkGenerator() {
  const [vertical, setVertical] = useState('realty');
  const [gatewayNumber, setGatewayNumber] = useState('971557357753');
  const [customMessage, setCustomMessage] = useState('');
  const [generatedLink, setGeneratedLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  // Get tenant_id from auth context
  const tenantId = localStorage.getItem('tenant_id') || '1';

  const generateLink = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/router/generate-link', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tenant_id: parseInt(tenantId),
          vertical,
          gateway_number: gatewayNumber,
          custom_message: customMessage,
        }),
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setGeneratedLink(data);
      } else {
        throw new Error(data.detail || 'Failed to generate link');
      }
    } catch (error) {
      console.error('Error generating link:', error);
      alert('خطا در ساخت لینک: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadQR = () => {
    if (generatedLink?.qr_code_url) {
      const link = document.createElement('a');
      link.href = generatedLink.qr_code_url;
      link.download = `qr-code-${vertical}-${tenantId}.png`;
      link.click();
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Share2 className="w-6 h-6 text-blue-600" />
          WhatsApp Deep Link Generator
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          لینک اختصاصی واتساپ برای مشتریان خود بسازید
        </p>
      </div>

      {/* Form */}
      <div className="space-y-4 mb-6">
        {/* Vertical Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Vertical
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'realty', label: '🏠 املاک', color: 'blue' },
              { value: 'expo', label: '🎪 نمایشگاه', color: 'purple' },
              { value: 'support', label: '💬 پشتیبانی', color: 'green' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => setVertical(option.value)}
                className={`p-3 rounded-lg border-2 transition-all ${
                  vertical === option.value
                    ? `border-${option.color}-500 bg-${option.color}-50 text-${option.color}-700`
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Gateway Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            شماره واتساپ Gateway
          </label>
          <input
            type="text"
            value={gatewayNumber}
            onChange={(e) => setGatewayNumber(e.target.value)}
            placeholder="971557357753"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-500 mt-1">
            شماره مشترک که روی سرور WAHA شما فعال است
          </p>
        </div>

        {/* Custom Message */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            پیام سفارشی (اختیاری)
          </label>
          <textarea
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            placeholder="سلام، می‌خواستم درباره املاک دبی سوال کنم..."
            rows="3"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Generate Button */}
        <button
          onClick={generateLink}
          disabled={loading}
          className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium py-3 px-6 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              در حال ساخت...
            </>
          ) : (
            <>
              <Share2 className="w-5 h-5" />
              ساخت لینک اختصاصی
            </>
          )}
        </button>
      </div>

      {/* Generated Link Display */}
      {generatedLink && (
        <div className="bg-gradient-to-br from-green-50 to-blue-50 border-2 border-green-200 rounded-lg p-6 space-y-4">
          {/* Success Message */}
          <div className="flex items-center gap-2 text-green-700">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">لینک با موفقیت ساخته شد!</span>
          </div>

          {/* Deep Link */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              لینک اختصاصی واتساپ:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={generatedLink.deep_link}
                readOnly
                className="flex-1 px-4 py-2 bg-white border border-gray-300 rounded-lg font-mono text-sm"
              />
              <button
                onClick={() => copyToClipboard(generatedLink.deep_link)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-all"
              >
                {copied ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    کپی شد
                  </>
                ) : (
                  <>
                    <Copy className="w-4 h-4" />
                    کپی
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Preview Text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              متن نمایش:
            </label>
            <div className="bg-white p-3 rounded-lg border border-gray-200">
              <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                {generatedLink.preview_text}
              </pre>
            </div>
          </div>

          {/* QR Code */}
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0">
              <img
                src={generatedLink.qr_code_url}
                alt="QR Code"
                className="w-32 h-32 border-2 border-gray-300 rounded-lg"
              />
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-gray-800 mb-2">QR Code</h4>
              <p className="text-sm text-gray-600 mb-3">
                مشتریان می‌توانند این کد را اسکن کنند و مستقیماً با شما در واتساپ ارتباط برقرار کنند
              </p>
              <button
                onClick={downloadQR}
                className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-900 text-white rounded-lg transition-all"
              >
                <Download className="w-4 h-4" />
                دانلود QR Code
              </button>
            </div>
          </div>

          {/* Usage Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              نحوه استفاده:
            </h4>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>این لینک را در ایمیل، SMS یا شبکه‌های اجتماعی با مشتری share کنید</li>
              <li>وقتی مشتری روی لینک کلیک کند، واتساپ باز می‌شود</li>
              <li>پیام از قبل تایپ شده - مشتری فقط send می‌کند</li>
              <li>از اون لحظه، تمام پیام‌های مشتری به ربات شما route می‌شود</li>
              <li>سشن 24 ساعته است - بعد از 24 ساعت بی‌فعالیتی، expire می‌شود</li>
            </ul>
          </div>
        </div>
      )}

      {/* Stats Preview */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">-</div>
          <div className="text-sm text-gray-600">Active Sessions</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">-</div>
          <div className="text-sm text-gray-600">Total Clicks</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">24h</div>
          <div className="text-sm text-gray-600">Session Duration</div>
        </div>
      </div>
    </div>
  );
}
