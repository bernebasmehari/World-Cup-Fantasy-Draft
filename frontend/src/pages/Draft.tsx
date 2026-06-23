import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import './Draft.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const ROUNDS = 5

interface User  { id: number; name: string; room_code: string; draft_order: number | null }
interface Team  { id: number; name: string; points: number }
interface Pick  { id: number; user_id: number; team_id: number; pick_number: number; room_code: string }

// Given a 1-based pick number and player count, return which player index (0-based) is picking.
// Snake: even rounds go left→right, odd rounds go right→left.
function playerForPick(pickNum: number, n: number): number {
  const idx   = pickNum - 1
  const round = Math.floor(idx / n)
  const pos   = idx % n
  return round % 2 === 0 ? pos : n - 1 - pos
}

// Given a round (0-based) and a player column index (0-based), return the pick number for that cell.
function pickNumForCell(round: number, col: number, n: number): number {
  return round % 2 === 0
    ? round * n + col + 1
    : round * n + (n - 1 - col) + 1
}

export default function Draft() {
  const [searchParams] = useSearchParams()
  const roomCode = searchParams.get('room') ?? ''
  const myName   = searchParams.get('name') ?? ''

  const [users,     setUsers]     = useState<User[]>([])
  const [teams,     setTeams]     = useState<Team[]>([])
  const [picks,     setPicks]     = useState<Pick[]>([])
  const [selected,  setSelected]  = useState<number | null>(null)
  const [loading,   setLoading]   = useState(true)

  const fetchPicks = useCallback(async () => {
    const data: Pick[] = await fetch(`${API}/draft-teams/${roomCode}`).then(r => r.json())
    setPicks(data)
  }, [roomCode])

  useEffect(() => {
    async function init() {
      const [allUsers, allTeams, roomPicks]: [User[], Team[], Pick[]] = await Promise.all([
        fetch(`${API}/users`).then(r => r.json()),
        fetch(`${API}/teams`).then(r => r.json()),
        fetch(`${API}/draft-teams/${roomCode}`).then(r => r.json()),
      ])
      const roomUsers = allUsers
        .filter(u => u.room_code === roomCode)
        .sort((a, b) => a.id - b.id)
      setUsers(roomUsers)
      setTeams(allTeams)
      setPicks(roomPicks)
      setLoading(false)
    }
    init()
    const interval = setInterval(fetchPicks, 2000)
    return () => clearInterval(interval)
  }, [roomCode, fetchPicks])

  if (loading)   return <p>Loading draft…</p>
  if (!roomCode) return <p>No room code — go back to Home and join a room.</p>

  const n          = users.length
  const totalPicks = n * ROUNDS
  const nextPick   = picks.length + 1
  const done       = picks.length >= totalPicks

  const activeColIdx = done ? -1 : playerForPick(nextPick, n)
  const myColIdx     = users.findIndex(u => u.name === myName)
  const isMyTurn     = !done && activeColIdx === myColIdx && n > 0

  // pick_number → team name
  const teamForPick = new Map<number, string>()
  for (const p of picks) {
    const t = teams.find(t => t.id === p.team_id)
    if (t) teamForPick.set(p.pick_number, t.name)
  }

  const draftedIds = new Set(picks.map(p => p.team_id))
  const available  = teams.filter(t => !draftedIds.has(t.id))

  async function handlePick() {
    if (!selected || !isMyTurn) return
    await fetch(`${API}/draft-teams`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id:     users[myColIdx].id,
        team_id:     selected,
        pick_number: nextPick,
        room_code:   roomCode,
      }),
    })
    setSelected(null)
    fetchPicks()
  }

  return (
    <div className="draft-room">
      <h1>Room: {roomCode}</h1>

      <p className="clock">
        {n === 0 ? (
          'Waiting for players to join…'
        ) : done ? (
          '🏁 Draft complete!'
        ) : (
          <>On the clock: <strong>{users[activeColIdx]?.name}</strong>{isMyTurn && ' — your pick!'}</>
        )}
      </p>

      {/* ── Draft grid ── */}
      {n > 0 && (
        <div className="grid-scroll">
          <table className="draft-grid">
            <thead>
              <tr>
                <th></th>
                {users.map(u => (
                  <th key={u.id} className={u.name === myName ? 'my-col' : ''}>
                    {u.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: ROUNDS }, (_, round) => (
                <tr key={round}>
                  <td className="round-label">Round {round + 1}</td>
                  {users.map((u, col) => {
                    const pn       = pickNumForCell(round, col, n)
                    const teamName = teamForPick.get(pn)
                    const isNext   = !done && pn === nextPick
                    const isMyCell = u.name === myName

                    return (
                      <td
                        key={col}
                        className={[
                          isNext               ? 'active-cell' : '',
                          teamName && isMyCell ? 'my-pick'     : '',
                          teamName && !isMyCell ? 'filled'     : '',
                        ].filter(Boolean).join(' ')}
                      >
                        {teamName ?? (isNext ? '⏳' : '')}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Team picker (only shown on your turn) ── */}
      {isMyTurn && (
        <div className="picker">
          <h3>Your pick — choose a team</h3>
          <select value={selected ?? ''} onChange={e => setSelected(Number(e.target.value))}>
            <option value=''>— select a team —</option>
            {available.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <button onClick={handlePick} disabled={!selected}>
            Draft Team
          </button>
        </div>
      )}

      {!isMyTurn && !done && n > 0 && (
        <p className="waiting">Waiting for {users[activeColIdx]?.name} to pick…</p>
      )}
    </div>
  )
}
