import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface TeamEntry { team: string; points: number }
interface UserEntry { user: string; total_points: number; teams: TeamEntry[] }
interface SyncResult { status: string; updated: number; skipped: string[] }

export default function Leaderboard() {
  const [searchParams] = useSearchParams()
  const [roomInput, setRoomInput] = useState(searchParams.get('room') ?? '')
  const [roomCode,  setRoomCode]  = useState(searchParams.get('room') ?? '')
  const [rows,      setRows]      = useState<UserEntry[]>([])
  const [loading,   setLoading]   = useState(false)
  const [syncing,   setSyncing]   = useState(false)
  const [syncMsg,   setSyncMsg]   = useState('')
  const [error,     setError]     = useState('')

  const loadLeaderboard = useCallback((code: string) => {
    if (!code) return
    setLoading(true)
    setError('')
    fetch(`${API}/leaderboard/${code}`)
      .then(r => r.json())
      .then(data => { setRows(data); setLoading(false) })
      .catch(() => { setError('Failed to load leaderboard.'); setLoading(false) })
  }, [])

  useEffect(() => { loadLeaderboard(roomCode) }, [roomCode, loadLeaderboard])

  async function handleSync() {
    setSyncing(true)
    setSyncMsg('')
    setError('')
    try {
      const r = await fetch(`${API}/sync-standings`, { method: 'POST' })
      const data: SyncResult = await r.json()
      if (!r.ok) {
        setError((data as any).detail ?? 'Sync failed.')
      } else {
        const skipped = data.skipped.length > 0
          ? ` (${data.skipped.length} unmatched: ${data.skipped.join(', ')})`
          : ''
        setSyncMsg(`Synced ${data.updated} teams from FIFA.${skipped}`)
        // Refresh leaderboard after sync
        if (roomCode) loadLeaderboard(roomCode)
      }
    } catch {
      setError('Could not reach the backend.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div>
      <h1>Leaderboard</h1>

      {/* Room loader + FIFA sync button */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          placeholder="Room code"
          value={roomInput}
          onChange={e => setRoomInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && setRoomCode(roomInput.trim())}
        />
        <button onClick={() => setRoomCode(roomInput.trim())}>Load</button>

        <button
          onClick={handleSync}
          disabled={syncing}
          style={{
            marginLeft: '0.5rem',
            background: syncing ? '#333' : '#1a5c1a',
            color: '#9f9',
            border: '1px solid #3a9a3a',
            padding: '0.35rem 0.9rem',
            borderRadius: 4,
            cursor: syncing ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
          }}
        >
          {syncing ? 'Syncing…' : '⟳ Refresh from FIFA'}
        </button>
      </div>

      {syncMsg && (
        <p style={{ color: '#9f9', fontSize: '0.85rem', marginBottom: '1rem' }}>{syncMsg}</p>
      )}

      {loading && <p>Loading…</p>}
      {error   && <p style={{ color: 'crimson' }}>{error}</p>}

      {!loading && rows.length > 0 && (
        <table style={{ borderCollapse: 'collapse', minWidth: 500 }}>
          <thead>
            <tr>
              <th style={th}>#</th>
              <th style={th}>Player</th>
              <th style={th}>Points</th>
              <th style={th}>Teams</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={row.user}>
                <td style={td}>{i + 1}</td>
                <td style={td}><strong>{row.user}</strong></td>
                <td style={{ ...td, fontWeight: 700, color: '#a0f0a0' }}>
                  {row.total_points.toFixed(1)}
                </td>
                <td style={td}>
                  {row.teams.map(t => `${t.team} (${t.points.toFixed(1)})`).join(' · ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {!loading && roomCode && rows.length === 0 && !error && (
        <p style={{ color: '#888' }}>No players found in room "{roomCode}".</p>
      )}
    </div>
  )
}

const th: React.CSSProperties = {
  border: '1px solid #444', padding: '0.45rem 0.75rem',
  background: '#1a1a2e', color: '#fff', textAlign: 'left',
}
const td: React.CSSProperties = {
  border: '1px solid #444', padding: '0.45rem 0.75rem',
}
