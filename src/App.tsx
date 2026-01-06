import { useState, useEffect } from 'react';
import { Sidebar, Header } from './layout/Layout';
import Dashboard from './pages/Dashboard';
import Portfolio from './pages/Portfolio';
import Strategies from './pages/Strategies';
import LiveMarket from './pages/LiveMarket';
import HistoricalData from './pages/HistoricalData';
import Orders from './pages/Orders';
import TradingBot from './pages/TradingBot';
import Backtesting from './pages/Backtesting';
import Login from './pages/Login';
import { Toaster } from 'sonner';

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/status');
      const data = await response.json();
      setIsAuthenticated(data.is_authenticated);

      // Check for login success param in URL
      const params = new URLSearchParams(window.location.search);
      if (params.get('login') === 'success') {
        // Clear URL param
        window.history.replaceState({}, '', window.location.pathname);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    }
  };

  if (isAuthenticated === null) {
    return <div className="flex h-screen items-center justify-center bg-zinc-950 text-zinc-500">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  const renderContent = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard onNavigate={setActivePage} />;
      case 'portfolio': return <Portfolio />;
      case 'strategies': return <Strategies />;
      case 'trading-bot': return <TradingBot />;
      case 'live': return <LiveMarket />;
      case 'historical': return <HistoricalData />;
      case 'orders': return <Orders />;
      case 'backtesting': return <Backtesting />;
      case 'settings': return (
        <div className="h-full w-full p-4 space-y-4">
          <div className="bg-zinc-950 border border-zinc-800 rounded-xl p-8 text-center">
            <h2 className="text-2xl font-bold text-zinc-100 mb-4">Settings</h2>
            <p className="text-zinc-500">API Settings and Configuration coming soon...</p>
          </div>
        </div>
      );
      default: return <Dashboard onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden text-[15px]">
      <Toaster position="top-right" richColors />
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        <Header
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        />
        <main className="flex-1 overflow-y-auto bg-black/20">
          {renderContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
