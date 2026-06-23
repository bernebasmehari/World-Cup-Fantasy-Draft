import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { Account } from '../App'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface User  { id: number; name: string; room_code: string }
interface Team  { id: number; name: string; points: number; furthest_round: string }
interface Pick  { id: number; user_id: number; team_id: number; pick_number: number }

interface Props { account: Account | null }

export default function Roster({ account }: Props) {
  const [searchParams] = useSearchParams()
  const [roomInput, setRoomInput] = useState(searchParams.get('room') ?? '')
  const [roomCode,  setRoomCode]  = useState(searchParams.get('room') ?? '')
  const [roster,    setRoster]    = useState<{ team: Team; pick: number }[]>([])
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState('')

  useEffect(() => {
    if (!roomCode || !account) return
    setLoading(true)
    setError('')

    Promise.all([
      fetch(`${API}/users`).then(r => r.json()),
      fetch(`${API}/teams`).then(r => r.json()),
      fetch(`${API}/draft-teams/${roomCode}`).then(r => r.json()),
    ]).then(([allUsers, allTeams, picks]: [User[], Team[], Pick[]]) => {
      const me = allUsers.find(u => u.name === account.username && u.room_code === roomCode)
      if (!me) { setError(`You haven't joined room "${roomCode}" yet.`); setLoading(false); return }

      const myPicks = picks
        .filter(p => p.user_id === me.id)
        .sort((a, b) => a.pick_number - b.pick_number)
        .map(p => {
          const team = allTeams.find(t => t.id === p.team_id)
          return team ? { team, pick: p.pick_number } : null
        })
        .filter(Boolean) as { team: Team; pick: number }[]

      setRoster(myPicks)
      setLoading(false)
    }).catch(() => { setError('Failed to load roster.'); setLoading(false) })
  }, [roomCode, account])

  if (!account) {
    return (
      <div>
        <h1>My Roster</h1>
        <p>Log in first to view your roster.</p>
      </div>
    )
  }

  const total = roster.reduce((sum, r) => sum + r.team.points, 0)

  return (
    <div>
      <h1>My Roster — {account.username}</h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <input
          placeholder="Room code"
          value={roomInput}
          onChange={e => setRoomInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && setRoomCode(roomInput.trim())}
        />
        <button onClick={() => setRoomCode(roomInput.trim())}>Load</button>
      </div>

      {loading && <p>Loading…</p>}
      {error   && <p style={{ color: 'crimson' }}>{error}</p>}

      {!loading && roster.length > 0 && (
        <>
          <table style={{ borderCollapse: 'collapse', minWidth: 360 }}>
            <thead>
              <tr>
                <th style={th}>Pick</th>
                <th style={th}>Team</th>
                <th style={th}>Stage reached</th>
                <th style={th}>Points</th>
              </tr>
            </thead>
            <tbody>
              {roster.map(({ team, pick }) => (
                <tr key={team.id}>
                  <td style={td}>{pick}</td>
                  <td style={td}><strong>{team.name}</strong></td>
                  <td style={td}>{team.furthest_round.replace(/_/g, ' ')}</td>
                  <td style={td}>{team.points.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={3} style={{ ...td, fontWeight: 700, textAlign: 'right' }}>Total</td>
                <td style={{ ...td, fontWeight: 700 }}>{total.toFixed(1)}</td>
              </tr>
            </tfoot>
          </table>
        </>
      )}

      {!loading && roomCode && roster.length === 0 && !error && (
        <p style={{ color: '#888' }}>No picks found for you in room "{roomCode}".</p>
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
