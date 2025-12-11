import { useState } from 'react'
import { Menu, X } from 'lucide-react'

const MobileMenuButton = ({ sidebar, setSidebarOpen }) => {
  const [isOpen, setIsOpen] = useState(false)

  const toggleMenu = () => {
    setIsOpen(!isOpen)
    setSidebarOpen?.(!isOpen)
  }

  // Only show on mobile
  if (window.innerWidth > 640) return null

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleMenu}
        className="mobile-menu-btn fixed top-4 left-4 z-50 bg-gradient-to-r from-gold-500 to-orange-500 text-navy-900 p-3 rounded-lg shadow-lg md:hidden"
        aria-label="Toggle menu"
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <Menu className="w-6 h-6" />
        )}
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={toggleMenu}
        />
      )}
    </>
  )
}

export default MobileMenuButton
