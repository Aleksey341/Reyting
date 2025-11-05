import { useEffect, useState } from 'react'
import { getHealth } from '../api'

export default function HealthBadge() {
  const [ok, setOk] = useState<boolean | null>(null)
  const [msg, setMsg] = useState<string>('')

  useEffect(() => {
    getHealth()
      .then(() => { setOk(true); setMsg('OK') })
      .catch(e => { setOk(false); setMsg(e?.message || 'Error') })
  }, [])

  if (ok === null) return <span className="badge">Проверка…</span>
  return <span className={`badge ${ok ? 'ok' : 'fail'}`}>Бэкенд: {msg}</span>
}
