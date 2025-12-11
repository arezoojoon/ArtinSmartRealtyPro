
import { useState } from 'react'
import { Layout } from '../components/Layout'
import { QrCode, Download, Smartphone, MessageCircle } from 'lucide-react'
import QRCodeReact from 'qrcode.react'

const QRGenerator = () => {
  const [telegramBot, setTelegramBot] = useState('@YourBoothBot')
  const [whatsappNumber, setWhatsappNumber] = useState('+971501234567')

  const telegramLink = `https://t.me/${telegramBot.replace('@', '')}`
  const whatsappLink = `https://wa.me/${whatsappNumber.replace(/\D/g, '')}`

  const downloadQR = (elementId, filename) => {
    const canvas = document.querySelector(`#${elementId} canvas`)
    if (canvas) {
      const url = canvas.toDataURL('image/png')
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
    }
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <QrCode className="w-8 h-8 text-gold-500" />
            QR Code Generator
          </h1>
          <p className="text-gray-400">
            Generate QR codes for Telegram and WhatsApp booth access
          </p>
        </div>

        {/* Instructions Card */}
        <div className="glass-card rounded-2xl p-6 border-l-4 border-gold-500">
          <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Smartphone className="w-5 h-5 text-gold-500" />
            How to Use
          </h3>
          <ul className="space-y-2 text-gray-300">
            <li className="flex items-start gap-2">
              <span className="text-gold-500 font-bold">1.</span>
              <span>Configure your bot usernames and phone numbers below</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gold-500 font-bold">2.</span>
              <span>Download the generated QR codes as PNG files</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gold-500 font-bold">3.</span>
              <span>Print and display at your exhibition booth</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gold-500 font-bold">4.</span>
              <span>Visitors scan to start chatting with your bot</span>
            </li>
          </ul>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Telegram QR */}
          <div className="glass-card glass-card-hover rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-500/20">
                <MessageCircle className="w-6 h-6 text-blue-500" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Telegram Bot</h3>
                <p className="text-sm text-gray-400">Connect via Telegram</p>
              </div>
            </div>

            {/* Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-white/70 mb-2">
                Bot Username
              </label>
              <input
                type="text"
                value={telegramBot}
                onChange={(e) => setTelegramBot(e.target.value)}
                placeholder="@YourBoothBot"
                className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors"
              />
              <p className="text-xs text-gray-500 mt-2">
                Link: <code className="text-gold-500">{telegramLink}</code>
              </p>
            </div>

            {/* QR Code */}
            <div className="bg-white p-6 rounded-2xl mb-6 flex items-center justify-center" id="telegram-qr">
              <QRCodeReact
                value={telegramLink}
                size={256}
                level="H"
                includeMargin={true}
                fgColor="#0088cc"
              />
            </div>

            {/* Download Button */}
            <button
              onClick={() => downloadQR('telegram-qr', 'telegram-booth-qr.png')}
              className="w-full px-6 py-3 btn-gold rounded-xl flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Telegram QR
            </button>
          </div>

          {/* WhatsApp QR */}
          <div className="glass-card glass-card-hover rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-green-500/20">
                <MessageCircle className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">WhatsApp Bot</h3>
                <p className="text-sm text-gray-400">Connect via WhatsApp</p>
              </div>
            </div>

            {/* Input */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-white/70 mb-2">
                WhatsApp Number
              </label>
              <input
                type="text"
                value={whatsappNumber}
                onChange={(e) => setWhatsappNumber(e.target.value)}
                placeholder="+971501234567"
                className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors"
              />
              <p className="text-xs text-gray-500 mt-2">
                Link: <code className="text-gold-500">{whatsappLink}</code>
              </p>
            </div>

            {/* QR Code */}
            <div className="bg-white p-6 rounded-2xl mb-6 flex items-center justify-center" id="whatsapp-qr">
              <QRCodeReact
                value={whatsappLink}
                size={256}
                level="H"
                includeMargin={true}
                fgColor="#25D366"
              />
            </div>

            {/* Download Button */}
            <button
              onClick={() => downloadQR('whatsapp-qr', 'whatsapp-booth-qr.png')}
              className="w-full px-6 py-3 btn-gold rounded-xl flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download WhatsApp QR
            </button>
          </div>
        </div>

        {/* Tips Card */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">💡 Printing Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-300">
            <div>
              <p className="text-gold-500 font-bold mb-2">Size</p>
              <p>Recommended minimum: 10cm x 10cm for easy scanning</p>
            </div>
            <div>
              <p className="text-gold-500 font-bold mb-2">Quality</p>
              <p>Use high-quality printing (300+ DPI) for best results</p>
            </div>
            <div>
              <p className="text-gold-500 font-bold mb-2">Material</p>
              <p>Laminate or use weather-resistant material for outdoor use</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default QRGenerator
