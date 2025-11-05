import { useEffect, useState } from 'react'
import { getRating, RatingItem } from '../api'

export default function RatingTable() {
  const [items, setItems] = useState<RatingItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getRating(page, 50)
      .then(res => {
        setItems(res.data || [])
        setError(null)
      })
      .catch(err => {
        setError(err?.message || 'Ошибка загрузки рейтинга')
        setItems([])
      })
      .finally(() => setLoading(false))
  }, [page])

  if (loading) return <div className="loading">Загрузка…</div>
  if (error) return <div className="error">Ошибка: {error}</div>
  if (!items || items.length === 0) {
    return <div className="empty">Нет данных</div>
  }

  return (
    <div className="rating-table-container">
      <table className="rating-table">
        <thead>
          <tr>
            <th>Место</th>
            <th>Муниципальное образование</th>
            <th>Оценка</th>
            <th>Зона</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, idx) => (
            <tr key={item.mo_id}>
              <td className="rank">{(page - 1) * 50 + idx + 1}</td>
              <td className="name">{item.mo_name}</td>
              <td className="score">{item.score_total?.toFixed(2) || 'N/A'}</td>
              <td className="zone">{item.zone || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
          className="btn"
        >
          ← Предыдущая
        </button>
        <span className="page-info">Страница {page}</span>
        <button
          disabled={!items || items.length < 50}
          onClick={() => setPage(p => p + 1)}
          className="btn"
        >
          Следующая →
        </button>
      </div>
    </div>
  )
}
