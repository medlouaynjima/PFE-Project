import React, { useState } from 'react';
import { Shield, Eye, EyeOff, User, Lock, ArrowRight, AlertCircle } from 'lucide-react';

interface LoginPageProps {
  onLogin: (userType: 'adherent' | 'medecin' | 'admin', userId: string, userName?: string) => void;
  onBackToHome: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onBackToHome }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    userType: 'adherent' as 'adherent' | 'medecin' | 'admin'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Préparer le corps de la requête selon le backend (email OU username)
      const body: any = {
        password: formData.password,
        userType: formData.userType, // <-- AJOUTE CECI
      };
      if (formData.email.includes('@')) {
        body.email = formData.email;
    } else {
        body.username = formData.email;
      }

      const response = await fetch('http://localhost:8089/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        if (response.status === 401) {
      setError('Email ou mot de passe incorrect');
        } else {
          setError('Erreur lors de la connexion');
        }
        setIsLoading(false);
        return;
      }

      // Le backend renvoie maintenant un JSON avec tous les IDs
      const data = await response.json();
      localStorage.setItem('token', data.token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('role', data.role);
      if (data.adherent_id) localStorage.setItem('adherent_id', data.adherent_id);
      if (data.medecin_id) localStorage.setItem('medecin_id', data.medecin_id);
      // Stocke le nom complet selon le type d'utilisateur
      let userName = '';
      if (data.role === 'ADHERENT' && data.nom && data.prenom) {
        userName = `${data.prenom} ${data.nom}`;
      } else if (data.role === 'MEDECIN' && data.nom && data.prenom) {
        userName = `${data.prenom} ${data.nom}`;
      } else if (data.username) {
        userName = data.username;
      }
      localStorage.setItem('user_name', userName);
      onLogin(data.role, data.user_id, userName);
    } catch (err) {
      setError('Erreur réseau ou serveur.');
    }
    setIsLoading(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
    if (error) setError('');
  };

  const userTypeLabels = {
    adherent: 'Adhérent',
    medecin: 'Professionnel de santé',
    admin: 'Administrateur'
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-green-50 dark:from-gray-900 dark:to-gray-800 dark:text-gray-100">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-600 to-green-600 rounded-xl shadow-lg">
              <Shield className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">I-Way Solutions</h1>
              <p className="text-sm text-gray-600">Portail Sécurisé</p>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Connexion à votre espace</h2>
          <p className="text-gray-600">Accédez à vos services de gestion des réclamations</p>
        </div>

        {/* Login Form */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-10 max-w-md w-full">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* User Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Type de compte
              </label>
              <div className="grid grid-cols-1 gap-2">
                {Object.entries(userTypeLabels).map(([value, label]) => (
                  <label key={value} className="relative">
                    <input
                      type="radio"
                      name="userType"
                      value={value}
                      checked={formData.userType === value}
                      onChange={handleInputChange}
                      className="sr-only"
                    />
                    <div className={`p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                      formData.userType === value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300 text-gray-700'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{label}</span>
                        <div className={`w-4 h-4 rounded-full border-2 ${
                          formData.userType === value
                            ? 'border-blue-500 bg-blue-500'
                            : 'border-gray-300'
                        }`}>
                          {formData.userType === value && (
                            <div className="w-full h-full rounded-full bg-white scale-50"></div>
                          )}
                        </div>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Email/Username Field */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Identifiant ou adresse email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="text" // <-- modifié ici
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  placeholder="Votre identifiant ou email"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Mot de passe
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-10 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-3 px-4 rounded-lg font-semibold transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  <span>Se connecter</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Additional Links */}
            <div className="text-center space-y-2">
              <a href="#" className="text-sm text-blue-600 hover:text-blue-700 transition-colors">
                Mot de passe oublié ?
              </a>
              <div className="text-sm text-gray-600">
                Pas encore de compte ?{' '}
                <a href="#" className="text-blue-600 hover:text-blue-700 font-medium transition-colors">
                  Créer un compte
                </a>
              </div>
            </div>
          </form>
        </div>

        {/* Back to Home */}
        <div className="text-center mt-6">
          <button
            onClick={onBackToHome}
            className="text-gray-600 hover:text-gray-800 transition-colors text-sm"
          >
            ← Retour à l'accueil
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;