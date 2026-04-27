import { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import About from './components/About';
import ChatInterface from './components/ChatInterface';
import LoginPage from './components/LoginPage';
import Footer from './components/Footer';
import SettingsPage from './components/SettingsPage';
import AdherentDashboard from './components/AdherentDashboard';
import MedecinDashboard from './components/MedecinDashboard';

function App() {
  const [currentView, setCurrentView] = useState<'home' | 'chat' | 'login' | 'settings' | 'adherent-dashboard' | 'medecin-dashboard'>('home');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userType, setUserType] = useState<'adherent' | 'medecin' | 'admin' | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);

  // Restore login state from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');
    const role = localStorage.getItem('role');
    const name = localStorage.getItem('user_name');
    if (token && userId && role) {
      setIsLoggedIn(true);
      setUserType(role as 'adherent' | 'medecin' | 'admin');
      setUserId(userId);
      setUserName(name);
    }
  }, []);

  const handleLogin = (type: 'adherent' | 'medecin' | 'admin', userId: string, name?: string) => {
    setIsLoggedIn(true);
    setUserType(type);
    setUserId(userId);
    setUserName(name || null);
    setCurrentView('home');
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setUserType(null);
    setUserName(null);
    setCurrentView('home');
  };

  // Handler for the "Démarrer une réclamation" button
  const handleStartChat = () => {
    if (isLoggedIn) {
      setCurrentView('chat');
    } else {
      setCurrentView('login');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 dark:from-gray-900 dark:to-gray-800 dark:text-gray-100">
      {currentView !== 'login' && currentView !== 'chat' && (
        <Header 
          currentView={currentView as "home" | "chat"} 
          onViewChange={setCurrentView}
          isLoggedIn={isLoggedIn}
          userType={userType}
          userName={userName}
          onLogout={handleLogout}
        />
      )}
      
      {currentView === 'login' ? (
        <LoginPage 
          onLogin={handleLogin}
          onBackToHome={() => setCurrentView('home')}
        />
      ) : currentView === 'home' ? (
        <main>
          <Hero onStartChat={handleStartChat} />
          <div id="about-section">
            <About />
          </div>
          <div id="contact-section" className="flex flex-col items-center justify-center py-20">
            <h2 className="text-2xl font-bold mb-4">Contactez-nous</h2>
            <p className="text-gray-700 mb-2">Email : contact@iway-solutions.com</p>
            <p className="text-gray-700 mb-2">Téléphone : 01 23 45 67 89</p>
            <p className="text-gray-700">Adresse : 123 rue de l'Innovation, Paris</p>
          </div>
        </main>
      ) : currentView === 'settings' ? (
        <SettingsPage 
          onBack={() => setCurrentView('home')}
          userType={userType}
          onGoToDashboard={() => {
            if (userType === 'adherent') setCurrentView('adherent-dashboard');
            else if (userType === 'medecin') setCurrentView('medecin-dashboard');
          }}
        />
      ) : currentView === 'adherent-dashboard' ? (
        <AdherentDashboard />
      ) : currentView === 'medecin-dashboard' ? (
        <MedecinDashboard />
      ) : (
        <ChatInterface 
          onBackToHome={() => setCurrentView('home')}
          userType={userType}
          isLoggedIn={isLoggedIn}
          userId={userId}
        />
      )}
      
      {currentView !== 'login' && currentView !== 'chat' && <Footer />}
    </div>
  );
}

export default App;