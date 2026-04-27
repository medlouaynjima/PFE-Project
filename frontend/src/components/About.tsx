import { Database, Zap, Target, CheckCircle } from 'lucide-react';

const About: React.FC = () => {
  return (
    <section className="py-24 bg-white dark:bg-gray-900 dark:text-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            À propos d'I-Way Solutions
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Depuis 2015, nous révolutionnons la gestion des assurances santé grâce à l'innovation technologique
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-16 items-center mb-20">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 mb-6">Notre Histoire</h3>
            <p className="text-gray-600 mb-6 leading-relaxed">
              En 2015, I-Way Solutions a été fondée grâce à une alliance entre une expertise approfondie 
              dans le domaine des assurances maladie et des professionnels des nouvelles technologies 
              de l'information et de la communication.
            </p>
            <p className="text-gray-600 mb-8 leading-relaxed">
              En quelques années, I-Way Solutions s'est imposée comme un innovateur dans le domaine 
              des assurances santé, spécialisée dans la gestion des sinistres de santé.
            </p>
            
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">2015</div>
                <div className="text-sm text-gray-600">Année de création</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-2">500+</div>
                <div className="text-sm text-gray-600">Clients accompagnés</div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-green-50 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-8">
            <h4 className="text-xl font-semibold text-gray-900 mb-6">Nos Services</h4>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium text-gray-900">Gestion déléguée</p>
                  <p className="text-sm text-gray-600">Prise en charge complète des activités de gestion</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium text-gray-900">Traitement des données</p>
                  <p className="text-sm text-gray-600">Saisie et traitement automatisé des sinistres</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-medium text-gray-900">Support back-office</p>
                  <p className="text-sm text-gray-600">Accompagnement des équipes d'assurance</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-600 to-green-600 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-12 text-white text-center">
          <h3 className="text-2xl md:text-3xl font-bold mb-6">
            Projet ChatBot de Gestion des Réclamations
          </h3>
          <p className="text-xl text-blue-100 mb-8 max-w-4xl mx-auto">
            Automatisation intelligente du processus de gestion des réclamations pour améliorer 
            l'efficacité et la satisfaction des utilisateurs
          </p>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white/10 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6">
              <Database className="w-8 h-8 text-blue-200 mx-auto mb-4" />
              <h4 className="font-semibold mb-2">Base de Données Existante</h4>
              <p className="text-sm text-blue-100">
                Utilisation des anciennes réclamations pour entraîner l'IA
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <Zap className="w-8 h-8 text-green-200 mx-auto mb-4" />
              <h4 className="font-semibold mb-2">Automatisation</h4>
              <p className="text-sm text-blue-100">
                Traitement automatique des réclamations courantes
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6">
              <Target className="w-8 h-8 text-orange-200 mx-auto mb-4" />
              <h4 className="font-semibold mb-2">Efficacité</h4>
              <p className="text-sm text-blue-100">
                Réduction des délais et optimisation des ressources
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;