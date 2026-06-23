import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Account } from '../App'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Props {
  account: Account | null
  onLogin: (a: Account) => void
}

export default function Home({ account, onLogin }: Props) {
  const [tab,      setTab]      = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [roomCode, setRoomCode] = useState('')
  const [error,    setError]    = useState('')
  const navigate = useNavigate()

  async function handleAuth() {
    setError('')
    const endpoint = tab === 'login' ? '/login' : '/register'
    const res  = await fetch(`${API}${endpoint}`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ username, password }),
    })
    const data = await res.json()
    if (res.ok) {
      onLogin(data)
      setUsername('')
      setPassword('')
    } else {
      setError(data.detail ?? 'Something went wrong.')
    }
  }

  async function handleJoinRoom() {
    if (!account || !roomCode.trim()) return
    setError('')
    const res = await fetch(`${API}/users`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name: account.username, room_code: roomCode.trim() }),
    })
    const data = await res.json()
    // Already in room is fine — just navigate
    if (res.ok || (res.status === 400 && data.detail?.includes('already exists'))) {
      navigate(`/draft?room=${encodeURIComponent(roomCode.trim())}&name=${encodeURIComponent(account.username)}`)
    } else {
      setError(data.detail ?? 'Failed to join room.')
    }
  }

  // ── Logged-in view ──────────────────────────────────────────────
  if (account) {
    return (
      <div>
        <h1>WorldDraft</h1>
        <p>Welcome back, <strong>{account.username}</strong>!</p>

        <h2>Join a draft room</h2>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
          <input
            placeholder="Room code"
            value={roomCode}
            onChange={e => setRoomCode(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleJoinRoom()}
          />
          <button onClick={handleJoinRoom}>Join Room</button>
        </div>

        <p style={{ color: '#888', fontSize: '0.9rem', marginTop: '0.25rem' }}>
          Or browse:{' '}
          <a href="/roster">My Roster</a> ·{' '}
          <a href="/leaderboard">Leaderboard</a>
        </p>

        {error && <p style={{ color: 'crimson' }}>{error}</p>}
      </div>
    )
  }

  // ── Logged-out view ─────────────────────────────────────────────
  return (
    <div>
      <h1>WorldDraft</h1>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <button
          onClick={() => { setTab('login'); setError('') }}
          style={{ fontWeight: tab === 'login' ? 700 : 400 }}
        >
          Log in
        </button>
        <button
          onClick={() => { setTab('register'); setError('') }}
          style={{ fontWeight: tab === 'register' ? 700 : 400 }}
        >
          Create account
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxWidth: 280 }}>
        <input
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAuth()}
        />
        <button onClick={handleAuth}>
          {tab === 'login' ? 'Log in' : 'Create account'}
        </button>
        {error && <p style={{ color: 'crimson', margin: 0 }}>{error}</p>}
      </div>
    </div>
  )
}
