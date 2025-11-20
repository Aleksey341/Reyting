import React, { useState, useEffect } from 'react';
import { ratingService } from '../services/api';

export default function RatingPage({ period }) {
  const [ratingData, setRatingData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sort, setSort] = useState('score_total');
  const [showZoneModal, setShowZoneModal] = useState(false);
  const [expandedBlocks, setExpandedBlocks] = useState({});
  const pageSize = 50;

  // Official Methodology Structure (16 criteria + 3 penalties)
  // ПУБЛИЧНЫЙ (PUBLIC): 9 criteria = 31 points max
  // ЗАКРЫТЫЙ (CLOSED): 8 criteria = 35 points max
  // Штрафы (PENALTIES): 3 criteria = -10 points max
  const blocksConfig = [
    {
      id: 1,
      name: 'ПУБЛИЧНЫЙ РЕЙТИНГ',
      ratingType: 'ПУБЛИЧНЫЙ',
      color: 'blue',
      maxPoints: 31,
      criteria: [
        // Block 1: Political Management (4 criteria = 14 points)
        { code: 'pub_1', number: '1', label: 'Поддержка руководства области', maxPoints: 3 },
        { code: 'pub_2', number: '2', label: 'Выполнение задач АГП', maxPoints: 5 },
        { code: 'pub_3', number: '3', label: 'Позиционирование главы МО', maxPoints: 3 },
        { code: 'pub_4', number: '4', label: 'Проектная деятельность', maxPoints: 3 },
        // Block 2: Care & Attention (3 criteria = 9 points)
        { code: 'pub_5', number: '5', label: 'Молодежь в добровольчестве', maxPoints: 3 },
        { code: 'pub_6', number: '6', label: 'Молодежь в Движении Первых', maxPoints: 3 },
        { code: 'pub_7', number: '7', label: 'Работа с ветеранами СВО', maxPoints: 3 },
        // Block 3: Development (2 criteria = 6 points)
        { code: 'pub_8', number: '8', label: 'Кадровый резерв', maxPoints: 3 },
        { code: 'pub_9', number: '9', label: 'Работа с грантами', maxPoints: 3 },
      ],
    },
    {
      id: 2,
      name: 'ЗАКРЫТЫЙ РЕЙТИНГ',
      ratingType: 'ЗАКРЫТЫЙ',
      color: 'purple',
      maxPoints: 35,
      criteria: [
        // Block 1: Political Management (5 criteria = 23 points)
        { code: 'closed_1', number: '10', label: 'Партийное мнение в администрации', maxPoints: 6 },
        { code: 'closed_2', number: '11', label: 'Альтернативное мнение в органе', maxPoints: 4 },
        { code: 'closed_3', number: '12', label: 'Целевые показатели АГП (уровень)', maxPoints: 5 },
        { code: 'closed_4', number: '13', label: 'Целевые показатели АГП (качество)', maxPoints: 5 },
        { code: 'closed_5', number: '14', label: 'Экономическая привлекательность', maxPoints: 3 },
        // Block 2: Care & Attention (2 criteria = 9 points)
        { code: 'closed_7', number: '15', label: 'Политическая деятельность ветеранов', maxPoints: 6 },
        // Block 3: Development (1 criterion = 2 points)
        { code: 'closed_8', number: '16', label: 'Проект "Гордость Липецкой земли"', maxPoints: 2 },
      ],
    },
  ];

  // Penalty criteria (reduce total score)
  const penaltyColumns = [
    { code: 'pen_1', number: 'П1', label: 'Конфликты с региональной властью', maxPoints: -3 },
    { code: 'pen_2', number: 'П2', label: 'Внутримуниципальные конфликты', maxPoints: -3 },
    { code: 'pen_3', number: 'П3', label: 'Правоохранительные органы', maxPoints: -5 },
  ];

  useEffect(() => {
    const fetchRating = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await ratingService.getRating(period, null, sort, currentPage, pageSize);
        setRatingData(response.data.data || []);
      } catch (err) {
        console.error('Error fetching rating:', err);
        setError('Ошибка загрузки рейтинга');
      } finally {
        setLoading(false);
      }
    };

    fetchRating();
  }, [period, sort, currentPage]);

  const getScoreColor = (score) => {
    if (score >= 53) return '#2ecc71'; // Зеленая
    if (score >= 29) return '#f39c12'; // Желтая
    return '#e74c3c'; // Красная
  };

  const getScoreTextColor = (score) => {
    if (score >= 53) return '#27ae60'; // Темно-зеленый
    if (score >= 29) return '#d68910'; // Темно-оранжевый
    return '#c0392b'; // Темно-красный
  };

  const getZoneLabel = (zone) => {
    const labels = {
      green: 'Зелёная',
      yellow: 'Жёлтая',
      red: 'Красная',
    };
    return labels[zone] || 'Нет данных';
  };

  // Получить баллы критерия из блока
  const getCriteriaScore = (item, criteriaCode) => {
    if (!item.blocks) return 0;
    for (const block of item.blocks) {
      for (const criteria of block.criteria || []) {
        if (criteria.code === criteriaCode) {
          return criteria.score || 0;
        }
      }
    }
    return 0;
  };

  // Получить баллы штрафа
  const getPenaltyScore = (item, penaltyCode) => {
    if (!item.penalties) return 0;
    for (const penalty of item.penalties) {
      if (penalty.code === penaltyCode) {
        return penalty.score || 0;
      }
    }
    return 0;
  };

  // Получить блок для критерия
  const getBlockIdForCriteria = (criteriaCode) => {
    for (const block of blocksConfig) {
      for (const criteria of block.criteria) {
        if (criteria.code === criteriaCode) {
          return block.id;
        }
      }
    }
    return null;
  };

  const toggleBlockExpand = (blockId) => {
    setExpandedBlocks(prev => ({
      ...prev,
      [blockId]: !prev[blockId]
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Загрузка рейтинга...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Рейтинг муниципальных образований</h2>
          <button
            onClick={() => setShowZoneModal(true)}
            className="px-4 py-2 bg-blue-100 text-blue-700 rounded-md text-sm hover:bg-blue-200"
          >
            ℹ️ Описание зон
          </button>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <label className="text-sm font-medium text-gray-700">Сортировать по:</label>
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setCurrentPage(1);
            }}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm"
          >
            <option value="score_total">Итоговый балл</option>
            <option value="score_public">Публичный рейтинг</option>
            <option value="mo_name">Название МО</option>
          </select>
        </div>

        {/* Таблица с горизонтальной прокруткой */}
        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b sticky top-0">
              {/* Первый ряд - основные колонки и блоки */}
              <tr>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[40px]">
                  №
                </th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[200px]">
                  Муниципальное образование
                </th>
                <th className="px-3 py-3 text-left font-semibold text-gray-700 bg-gray-50 min-w-[150px]">
                  ФИО главы
                </th>

                {/* Блоки критериев */}
                {blocksConfig.map((block) => (
                  <th
                    key={block.id}
                    colSpan={block.criteria.length}
                    className={`px-3 py-3 text-center font-semibold text-gray-700 border-l border-r border-gray-300 ${
                      block.color === 'blue'
                        ? 'bg-blue-50'
                        : block.color === 'green'
                        ? 'bg-green-50'
                        : 'bg-purple-50'
                    }`}
                  >
                    {block.name}
                  </th>
                ))}

                {/* Штрафы */}
                <th
                  colSpan={penaltyColumns.length}
                  className="px-3 py-3 text-center font-semibold text-gray-700 bg-red-50 border-l border-r border-gray-300"
                >
                  Штрафы
                </th>

                {/* Итоговый балл */}
                <th className="px-3 py-3 text-center font-semibold text-gray-700 bg-green-50 min-w-[80px]">
                  ИТОГ
                </th>
              </tr>

              {/* Второй ряд - названия критериев */}
              <tr>
                <th colSpan="3" className="px-3 py-2 bg-gray-50"></th>

                {/* Критерии для каждого блока */}
                {blocksConfig.map((block) =>
                  block.criteria.map((criteria) => (
                    <th
                      key={criteria.code}
                      className={`px-2 py-2 text-center font-medium border-r border-gray-200 text-sm ${
                        block.color === 'blue'
                          ? 'bg-blue-50 text-blue-900'
                          : block.color === 'green'
                          ? 'bg-green-50 text-green-900'
                          : 'bg-purple-50 text-purple-900'
                      }`}
                      title={criteria.label}
                    >
                      {criteria.number}
                    </th>
                  ))
                )}

                {/* Штрафы */}
                {penaltyColumns.map((col) => (
                  <th
                    key={col.code}
                    className="px-2 py-2 text-center font-medium bg-red-50 text-red-900 border-r border-gray-200 text-sm"
                    title={col.label}
                  >
                    {col.number}
                  </th>
                ))}

                <th className="px-3 py-2 bg-green-50"></th>
              </tr>
            </thead>

            <tbody>
              {ratingData.map((item, index) => (
                <tr key={item.mo_id} className="border-b hover:bg-gray-50">
                  {/* Номер */}
                  <td className="px-3 py-3 font-semibold text-gray-900 bg-white min-w-[40px]">
                    {(currentPage - 1) * pageSize + index + 1}
                  </td>

                  {/* Название МО */}
                  <td className="px-3 py-3 text-gray-900 font-medium bg-white min-w-[200px]">
                    {item.mo_name}
                  </td>

                  {/* ФИО главы */}
                  <td className="px-3 py-3 text-gray-700 bg-white min-w-[150px]">
                    {item.leader_name}
                  </td>

                  {/* Критерии по блокам */}
                  {blocksConfig.map((block) =>
                    block.criteria.map((criteria) => (
                      <td
                        key={criteria.code}
                        className={`px-2 py-3 text-center border-r border-gray-200 text-sm font-medium ${
                          block.color === 'blue'
                            ? 'bg-blue-50 text-gray-700'
                            : block.color === 'green'
                            ? 'bg-green-50 text-gray-700'
                            : 'bg-purple-50 text-gray-700'
                        }`}
                      >
                        {getCriteriaScore(item, criteria.code).toFixed(1)}
                      </td>
                    ))
                  )}

                  {/* Штрафы */}
                  {penaltyColumns.map((col) => (
                    <td
                      key={col.code}
                      className="px-2 py-3 text-center text-red-700 border-r border-gray-200 bg-red-50 text-sm font-medium"
                    >
                      {getPenaltyScore(item, col.code).toFixed(1)}
                    </td>
                  ))}

                  {/* Итоговый балл с цветовой дифференциацией */}
                  <td className="px-3 py-3 text-center font-bold min-w-[80px] bg-white">
                    <span
                      style={{
                        color: getScoreTextColor(item.score_total),
                        fontSize: '16px',
                        fontWeight: 'bold',
                        padding: '6px 12px',
                        borderRadius: '4px',
                        backgroundColor: getScoreColor(item.score_total) + '20',
                      }}
                    >
                      {item.score_total.toFixed(0)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Пагинация */}
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Показано {ratingData.length} МО
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-2 border rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              ← Назад
            </button>
            <button
              onClick={() => setCurrentPage(currentPage + 1)}
              disabled={ratingData.length < pageSize}
              className="px-3 py-2 border rounded-md text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              Далее →
            </button>
          </div>
        </div>
      </div>

      {/* Модальное окно с описанием зон */}
      {showZoneModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl w-full mx-4">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Описание зон</h3>
              <button
                onClick={() => setShowZoneModal(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6">
              {/* Зелёная зона */}
              <div className="border-l-4 border-green-500 pl-4 py-3 bg-green-50 rounded">
                <h4 className="font-bold text-green-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-green-500 rounded"></span>
                  Зелёная зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">53-66 баллов</p>
                <p className="text-gray-700">
                  <strong>Высокая устойчивость</strong> – Отставка маловероятна, глава МО обладает значительным ресурсом для управления и карьерного роста
                </p>
              </div>

              {/* Жёлтая зона */}
              <div className="border-l-4 border-yellow-500 pl-4 py-3 bg-yellow-50 rounded">
                <h4 className="font-bold text-yellow-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-yellow-500 rounded"></span>
                  Жёлтая зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">29-52 баллов</p>
                <p className="text-gray-700">
                  <strong>Условная устойчивость</strong> – Существуют риски, требующие коррекции управленческой или политической стратегии
                </p>
              </div>

              {/* Красная зона */}
              <div className="border-l-4 border-red-500 pl-4 py-3 bg-red-50 rounded">
                <h4 className="font-bold text-red-900 mb-2 flex items-center gap-2">
                  <span className="inline-block w-4 h-4 bg-red-500 rounded"></span>
                  Красная зона
                </h4>
                <p className="text-gray-700 font-semibold mb-2">0-28 баллов</p>
                <p className="text-gray-700">
                  <strong>Низкая устойчивость</strong> – Высокий риск отставки в среднесрочной перспективе, наличие серьёзных системных проблем
                </p>
              </div>
            </div>

            <button
              onClick={() => setShowZoneModal(false)}
              className="mt-6 w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
