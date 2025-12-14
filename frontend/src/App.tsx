import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Chatbot from './components/Chatbot';
import Dashboard from './pages/Dashboard';
import MapComponent from './components/MapComponent';
import LiveTracker from './pages/LiveTracker';
import AccessibilityPage from './pages/Accessibility';
import Login from './pages/Login';
import './i18n'; // Init i18n
import './index.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen flex flex-col relative">
          <Navbar />

          <main className="flex-1 container mx-auto p-4 animate-fade-in">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/map" element={<div className="h-[80vh]"><MapComponent /></div>} />
              <Route path="/tracker" element={<div className="h-[80vh]"><LiveTracker /></div>} />
              <Route path="/accessibility" element={<AccessibilityPage />} />
              <Route path="/login" element={<Login />} />
            </Routes>
          </main>

          <Chatbot />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
