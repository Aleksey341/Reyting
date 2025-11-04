import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();

  const menuItems = [
    { path: '/', label: 'Карта', icon: '🗺️' },
    { path: '/rating', label: 'Рейтинг', icon: '📊' },
    { path: '/analytics', label: 'Аналитика', icon: '📈' },
  ];

  return (
    <aside className="w-64 bg-gray-800 text-white min-h-screen">
      <nav className="p-6">
        <ul className="space-y-2">
          {menuItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-6 border-t border-gray-700 mt-8">
        <div className="text-xs text-gray-400 space-y-2">
          <p>📘 <strong>Справка:</strong></p>
          <ul className="space-y-1 text-gray-300">
            <li>🟢 Зелёная зона: 53-66 баллов</li>
            <li>🟡 Жёлтая зона: 29-52 балла</li>
            <li>🔴 Красная зона: 0-28 баллов</li>
          </ul>
        </div>
      </div>
    </aside>
  );
}
