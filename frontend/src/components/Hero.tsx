import React from 'react';
import { MessageSquare, Clock, Users, TrendingUp, ArrowRight } from 'lucide-react';

interface HeroProps {
  onStartChat: () => void;
}

const Hero: React.FC<HeroProps> = ({ onStartChat }) => {
  return (
    <section className="py-24 bg-white dark:bg-gray-900 dark:text-gray-100">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-6">
            <span className="w-2 h-2 bg-blue-400 rounded-full mr-2 animate-pulse"></span>
            Nouvelle Technologie IA - Gestion Automatisée des Réclamations
          </div>
          
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Assistant IA pour
            <span className="bg-gradient-to-r from-blue-600 to-green-600 bg-clip-text text-transparent block">
              Réclamations Santé
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto leading-relaxed">
            Automatisez le traitement de vos réclamations d'assurance santé avec notre IA avancée. 
            Réponses instantanées 24/7 pour adhérents et professionnels de santé.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button
              onClick={onStartChat}
              className="group bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 shadow-lg hover:shadow-xl transform hover:-translate-y-1 flex items-center space-x-2"
            >
              <MessageSquare className="w-5 h-5" />
              <span>Démarrer une réclamation</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            
            <div className="text-sm text-gray-500 flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span>Disponible 24/7</span>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Réponse Instantanée</h3>
            <p className="text-gray-600 leading-relaxed">
              Traitement automatique des réclamations courantes en moins de 30 secondes, disponible 24h/24.
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
              <Users className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Multi-Utilisateurs</h3>
            <p className="text-gray-600 leading-relaxed">
              Interface adaptée pour adhérents, médecins et professionnels de santé avec accès personnalisé.
            </p>
          </div>

          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-8 border border-gray-200 hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-6">
              <TrendingUp className="w-6 h-6 text-orange-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Efficacité Optimisée</h3>
            <p className="text-gray-600 leading-relaxed">
              Réduction de 80% du temps de traitement et amélioration de la satisfaction client.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;