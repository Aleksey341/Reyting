import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './index.css';
import MapPage from './pages/MapPage';
import RatingPage from './pages/RatingPage';
import AnalyticsPage from './pages/AnalyticsPage';
import Header from './components/Header';
import Sidebar from './components/Sidebar';

function App() {
  const [period, setPeriod] = useState('2024-01');
  const [periodType, setPeriodType] = useState('month'); // 'month', 'halfyear', 'year'
  const [showSidebar, setShowSidebar] = useState(true);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header
          period={period}
          setPeriod={setPeriod}
          periodType={periodType}
          setPeriodType={setPeriodType}
          onMenuToggle={() => setShowSidebar(!showSidebar)}
        />

        <div className="flex">
          {showSidebar && <Sidebar />}

          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<MapPage period={period} />} />
              <Route path="/map" element={<MapPage period={period} />} />
              <Route path="/rating" element={<RatingPage period={period} />} />
              <Route path="/analytics" element={<AnalyticsPage period={period} />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
