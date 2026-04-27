import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Plus, Menu, Trash2, MessageSquare, Settings, LogOut } from 'lucide-react';
import SettingsPage from './SettingsPage';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  onBackToHome: () => void;
  userType?: 'adherent' | 'medecin' | 'admin' | null;
  isLoggedIn?: boolean;
  userId?: string | null;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  onBackToHome, 
  userType = null,
}: ChatInterfaceProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'Réclamation consultation médecin',
      lastMessage: 'Merci pour votre aide avec ma réclamation',
      timestamp: new Date(Date.now() - 86400000)
    },
    {
      id: '2', 
      title: 'Remboursement médicaments',
      lastMessage: 'Quels documents dois-je fournir ?',
      timestamp: new Date(Date.now() - 172800000)
    }
  ]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const simulateTyping = () => {
    setIsTyping(true);
    return new Promise(resolve => {
      setTimeout(() => {
        setIsTyping(false);
        resolve(true);
      }, 1000 + Math.random() * 2000);
    });
  };

  const getBotResponse = (userMessage: string): string => {
    const message = userMessage.toLowerCase();
    
    if (message.includes('réclamation') || message.includes('remboursement')) {
      return 'Je comprends que vous souhaitez faire une réclamation. Pour traiter votre demande efficacement, j\'ai besoin de quelques informations :\n\n• Type de soins (consultation, médicaments, hospitalisation)\n• Date des soins\n• Montant de la facture\n• Numéro d\'adhérent\n\nPouvez-vous me fournir ces éléments ?';
    }
    
    if (message.includes('bulletin') || message.includes('soin')) {
      return 'Pour votre bulletin de soins, voici la procédure :\n\n1. **Documents requis** :\n   - Facture originale du professionnel de santé\n   - Prescription médicale (si applicable)\n   - Attestation de droits\n\n2. **Délai de traitement** : 48-72h pour les cas simples\n\n3. **Suivi** : Vous recevrez un email de confirmation avec le numéro de dossier\n\nAvez-vous tous ces documents ?';
    }
    
    if (message.includes('délai') || message.includes('temps')) {
      return 'Voici les délais de traitement selon le type de réclamation :\n\n• **Consultations médicales** : 24-48h\n• **Médicaments** : 48-72h  \n• **Hospitalisation** : 5-7 jours ouvrés\n• **Soins dentaires** : 3-5 jours ouvrés\n• **Optique** : 2-4 jours ouvrés\n\nLes réclamations complexes peuvent nécessiter un délai supplémentaire. Vous êtes notifié à chaque étape du processus.';
    }
    
    if (message.includes('médecin') || message.includes('docteur') || message.includes('professionnel')) {
      return 'Interface professionnelle de santé :\n\n• **Soumission groupée** : Traitez plusieurs réclamations simultanément\n• **Validation RPPS** : Vérification automatique de votre numéro professionnel\n• **Suivi patients** : Tableau de bord dédié pour vos patients\n• **Facturation directe** : Intégration avec les systèmes de facturation\n\nQuel service souhaitez-vous utiliser ?';
    }
    
    if (message.includes('statut') || message.includes('suivi')) {
      return 'Pour consulter le statut de votre réclamation :\n\n1. **Par numéro de dossier** : Saisissez votre référence\n2. **Par numéro d\'adhérent** : Accès à toutes vos réclamations\n3. **Notifications temps réel** : Activez les alertes SMS/Email\n\nStatuts possibles :\n• 🟡 En cours de traitement\n• 🔵 En attente de documents\n• 🟢 Validée - Remboursement en cours\n• ✅ Traitée - Remboursement effectué\n\nQuel numéro souhaitez-vous vérifier ?';
    }

    if (message.includes('bonjour') || message.includes('salut') || message.includes('hello')) {
      return `Bonjour ! Je suis l'assistant IA d'I-Way Solutions, spécialisé dans la gestion des réclamations d'assurance santé.\n\n${
        userType === 'medecin' 
          ? '👨‍⚕️ **Interface Professionnelle** : Vous avez accès aux outils de soumission groupée et de suivi patients.'
          : userType === 'admin'
          ? '⚙️ **Interface Administrateur** : Accès aux tableaux de bord et statistiques avancées.'
          : '👤 **Espace Adhérent** : Je peux vous aider avec vos réclamations et remboursements.'
      }\n\nComment puis-je vous assister aujourd'hui ?`;
    }

    return 'Je comprends votre demande. Pour vous fournir une assistance optimale, pouvez-vous me donner plus de détails ?\n\nJe peux vous aider avec :\n• Soumission de nouvelles réclamations\n• Suivi de dossiers existants\n• Questions sur les remboursements\n• Procédures et délais\n• Documents requis\n\nQue souhaitez-vous faire précisément ?';
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() === '') return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue('');

    // Create new conversation if none exists
    if (!currentConversationId && messages.length === 0) {
      const newConversation: Conversation = {
        id: Date.now().toString(),
        title: currentInput.length > 30 ? currentInput.substring(0, 30) + '...' : currentInput,
        lastMessage: currentInput,
        timestamp: new Date()
      };
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversationId(newConversation.id);
    }

    setIsTyping(true);
    try {
      const role = localStorage.getItem("role");
      const adherent_id = localStorage.getItem("adherent_id");
      const medecin_id = localStorage.getItem("medecin_id");
      const user_name = localStorage.getItem("user_name");

      let payload: any = { question: currentInput };
      if (role === "ADHERENT" && adherent_id) {
        payload.adherent_id = adherent_id;
        if (user_name) payload.adherent_name = user_name;
      } else if (role === "MEDECIN" && medecin_id) {
        payload.medecin_id = medecin_id;
        if (user_name) payload.medecin_name = user_name;
      }
      
      payload.role = role;

      console.log(payload);
      const response = await fetch('http://localhost:8000/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        content: data.response,
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
    const botResponse: Message = {
      id: (Date.now() + 1).toString(),
        content: "Erreur lors de la connexion à l'assistant. Veuillez réessayer.",
      isBot: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, botResponse]);
    }
    setIsTyping(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setCurrentConversationId(null);
  };

  const selectConversation = (conversationId: string) => {
    setCurrentConversationId(conversationId);
    // In a real app, load messages for this conversation
    setMessages([
      {
        id: '1',
        content: 'Voici la conversation précédente que vous avez sélectionnée.',
        isBot: true,
        timestamp: new Date()
      }
    ]);
  };

  const deleteConversation = (conversationId: string) => {
    setConversations(prev => prev.filter(conv => conv.id !== conversationId));
    if (currentConversationId === conversationId) {
      setCurrentConversationId(null);
      setMessages([]);
    }
  };

  const getUserTypeLabel = () => {
    if (userType === 'medecin') return 'Professionnel de santé';
    if (userType === 'admin') return 'Administrateur';
    return 'Adhérent';
  };

  const suggestedPrompts = [
    "Comment faire une réclamation de consultation ?",
    "Quels documents fournir pour un remboursement ?",
    "Vérifier le statut de ma réclamation",
    "Délais de traitement des dossiers"
  ];

  if (showSettings) {
    return (
      <SettingsPage 
        onBack={() => setShowSettings(false)}
        userType={userType}
      />
    );
  }

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900 dark:text-gray-100">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-gray-900 dark:bg-gray-800 text-white dark:text-gray-100 flex flex-col overflow-hidden`}>
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={startNewConversation}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouvelle réclamation</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                  currentConversationId === conversation.id
                    ? 'bg-gray-700'
                    : 'hover:bg-gray-800'
                }`}
                onClick={() => selectConversation(conversation.id)}
              >
                <div className="flex items-center space-x-2">
                  <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{conversation.title}</p>
                    <p className="text-xs text-gray-400 truncate">{conversation.lastMessage}</p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conversation.id);
                  }}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-600 rounded transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{getUserTypeLabel()}</p>
              <p className="text-xs text-gray-400">I-Way Solutions</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={() => setShowSettings(true)}
              className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span className="text-sm">Paramètres</span>
            </button>
            <button 
              onClick={onBackToHome}
              className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span className="text-sm">Quitter</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col dark:bg-gray-900">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5 text-gray-600" />
              </button>
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="font-semibold text-gray-900">Assistant I-Way</h1>
                  <p className="text-sm text-gray-500">Gestion des réclamations santé</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-600">En ligne</span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto dark:bg-gray-900">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="max-w-2xl mx-auto text-center p-8">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Bot className="w-8 h-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Assistant I-Way Solutions
                </h2>
                <p className="text-gray-600 mb-8">
                  Bonjour ! Je suis votre assistant IA spécialisé dans la gestion des réclamations d'assurance santé. 
                  Comment puis-je vous aider aujourd'hui ?
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {suggestedPrompts.map((prompt, index) => (
                    <button
                      key={index}
                      onClick={() => setInputValue(prompt)}
                      className="p-4 text-left bg-white border border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-sm transition-all"
                    >
                      <p className="text-sm text-gray-700">{prompt}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto p-4">
              <div className="space-y-6">
                {messages.map((message) => (
                  <div key={message.id}>
                  <div
                    className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
                  >
                    <div className={`flex items-start space-x-3 max-w-3xl ${message.isBot ? '' : 'flex-row-reverse space-x-reverse'}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.isBot 
                          ? 'bg-gradient-to-br from-blue-600 to-green-600' 
                          : 'bg-gray-700'
                      }`}>
                        {message.isBot ? (
                          <Bot className="w-4 h-4 text-white" />
                        ) : (
                          <User className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className={`px-4 py-3 rounded-2xl ${
                        message.isBot
                          ? 'bg-white border border-gray-200'
                          : 'bg-blue-600 text-white'
                      }`}>
                        <div className={`prose prose-sm max-w-none ${message.isBot ? 'text-gray-800' : 'text-white'}`}>
                            {(message.content ?? "").split('\n').map((line, index) => (
                            <p key={index} className={index > 0 ? 'mt-2' : ''}>{line}</p>
                          ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="flex justify-start">
                    <div className="flex items-start space-x-3 max-w-3xl">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-green-600 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-white border border-gray-300 rounded-2xl shadow-sm">
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Décrivez votre réclamation ou posez votre question..."
                className="w-full px-4 py-3 pr-12 border-0 rounded-2xl resize-none focus:ring-0 focus:outline-none dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-400"
                rows={1}
                style={{ maxHeight: '200px' }}
              />
              <button
                onClick={handleSendMessage}
                disabled={inputValue.trim() === '' || isTyping}
                className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              L'assistant IA peut faire des erreurs. Vérifiez les informations importantes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;