import React from 'react';
import { Link } from 'react-router-dom';

export default function Header({ period, setPeriod, periodEnd, setPeriodEnd, periodType, setPeriodType, onMenuToggle }) {

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onMenuToggle}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Дашборд Липецкой области
            </h1>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Период:</label>

              {/* Селектор типа периода */}
              <select
                value={periodType}
                onChange={(e) => setPeriodType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                <option value="month">Месяц</option>
                <option value="quarter">Квартал</option>
                <option value="halfyear">Полугодие</option>
                <option value="year">Год</option>
                <option value="custom">Свободный выбор</option>
              </select>

              {/* Выбор конкретного периода */}
              {periodType === 'month' && (
                <input
                  type="month"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              )}

              {periodType === 'quarter' && (
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="2024-01">2024 - Q1 (янв-мар)</option>
                  <option value="2024-04">2024 - Q2 (апр-июнь)</option>
                  <option value="2024-07">2024 - Q3 (июль-сен)</option>
                  <option value="2024-10">2024 - Q4 (окт-дек)</option>
                  <option value="2023-01">2023 - Q1 (янв-мар)</option>
                  <option value="2023-04">2023 - Q2 (апр-июнь)</option>
                  <option value="2023-07">2023 - Q3 (июль-сен)</option>
                  <option value="2023-10">2023 - Q4 (окт-дек)</option>
                </select>
              )}

              {periodType === 'halfyear' && (
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="2024-01">2024 - 1-е полугодие</option>
                  <option value="2024-07">2024 - 2-е полугодие</option>
                  <option value="2023-01">2023 - 1-е полугодие</option>
                  <option value="2023-07">2023 - 2-е полугодие</option>
                </select>
              )}

              {periodType === 'year' && (
                <select
                  value={period.substring(0, 4) + '-01'}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  <option value="2024-01">2024</option>
                  <option value="2023-01">2023</option>
                  <option value="2022-01">2022</option>
                </select>
              )}

              {periodType === 'custom' && (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">с</span>
                  <input
                    type="month"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600">по</span>
                  <input
                    type="month"
                    value={periodEnd}
                    onChange={(e) => setPeriodEnd(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm">
              <span className="text-gray-600">
                Версия: <span className="font-semibold">1.0</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
