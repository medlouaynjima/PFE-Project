import React, { useState } from 'react';
import { MessageSquare, Shield, ArrowLeft, User, LogOut, ChevronDown } from 'lucide-react';

interface HeaderProps {
  currentView: 'home' | 'chat';
  onViewChange: (view: 'home' | 'chat' | 'login') => void;
  isLoggedIn?: boolean;
  userType?: 'adherent' | 'medecin' | 'admin' | null;
  onLogout?: () => void;
  userName?: string | null;
}

const Header: React.FC<HeaderProps> = ({ 
  currentView, 
  onViewChange, 
  isLoggedIn = false, 
  userType = null,
  onLogout,
  userName = null
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const getUserTypeLabel = (type: string | null) => {
    switch ((type || '').toLowerCase()) {
      case 'adherent': return 'Adhérent';
      case 'medecin': return 'Professionnel de santé';
      case 'admin': return 'Administrateur';
      default: return 'Utilisateur';
    }
  };

  return (
    <header className="bg-white/95 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-blue-600 to-green-600 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">I-Way Solutions</h1>
              <p className="text-xs text-gray-600">Innovation en Assurance Santé</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center space-x-8">
            <button
              onClick={() => {
                onViewChange('home');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                currentView === 'home'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
              }`}
            >
              Accueil
            </button>
            <button
              onClick={() => {
                const aboutSection = document.getElementById('about-section');
                if (aboutSection) {
                  aboutSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              className="px-4 py-2 rounded-lg transition-all duration-200 text-gray-700 hover:text-blue-600 hover:bg-blue-50"
            >
              À propos
            </button>
            <button
              onClick={() => {
                const contactSection = document.getElementById('contact-section');
                if (contactSection) {
                  contactSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
              className="px-4 py-2 rounded-lg transition-all duration-200 text-gray-700 hover:text-blue-600 hover:bg-blue-50"
            >
              Contactez-nous
            </button>
            
            {isLoggedIn ? (
              <button
                onClick={() => onViewChange('chat')}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                  currentView === 'chat'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                <span>Assistant Réclamations</span>
              </button>
            ) : (
              <button
                onClick={() => onViewChange('login')}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all duration-200 shadow-md"
              >
                <User className="w-4 h-4" />
                <span>Se connecter</span>
              </button>
            )}
          </nav>

          {/* User Menu */}
          {isLoggedIn && (
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 px-3 py-2 text-gray-700 hover:text-blue-600 transition-colors"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="hidden md:block text-sm font-medium">
                  {userName || getUserTypeLabel(userType)}
                </span>
                <ChevronDown className="w-4 h-4" />
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{userName || getUserTypeLabel(userType)}</p>
                    <p className="text-xs text-gray-500">{getUserTypeLabel(userType)}</p>
                  </div>
                  <button
                    onClick={() => {
                      onViewChange('settings' as any);
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                  >
                    <User className="w-4 h-4" />
                    <span>Paramètres</span>
                  </button>
                  <button
                    onClick={() => {
                      onLogout?.();
                      setShowUserMenu(false);
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Se déconnecter</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {currentView === 'chat' && (
            <button
              onClick={() => onViewChange('home')}
              className="md:hidden flex items-center space-x-2 px-3 py-2 text-gray-700 hover:text-blue-600 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Retour</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;