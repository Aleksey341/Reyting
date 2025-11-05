import HealthBadge from './components/HealthBadge'
import RatingTable from './components/RatingTable'
import './styles.css'

export default function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>Рейтинг эффективности</h1>
        <p className="subtitle">Муниципальные образования Липецкой области</p>
        <HealthBadge />
      </header>

      <main className="main">
        <div className="container">
          <RatingTable />
        </div>
      </main>

      <footer className="footer">
        <p>© 2025 Анализ эффективности деятельности органов власти</p>
      </footer>
    </div>
  )
}
