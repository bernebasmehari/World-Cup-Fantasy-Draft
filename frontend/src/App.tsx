import { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, useNavigate } from 'react-router-dom'
import Home from './pages/Home'
import Draft from './pages/Draft'
import Roster from './pages/Roster'
import Leaderboard from './pages/Leaderboard'

export interface Account { id: number; username: string }

const STORAGE_KEY = 'worlddraft_user'

function NavBar({ account, onLogout }: { account: Account | null; onLogout: () => void }) {
  const navigate = useNavigate()

  function logout() {
    onLogout()
    navigate('/')
  }

  return (
    <nav style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
      <Link to="/">Home</Link>
      <Link to="/draft">Draft</Link>
      <Link to="/roster">Roster</Link>
      <Link to="/leaderboard">Leaderboard</Link>
      {account && (
        <span style={{ marginLeft: 'auto', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span style={{ color: '#a0a0ff', fontWeight: 600 }}>👤 {account.username}</span>
          <button
            onClick={logout}
            style={{ padding: '0.2rem 0.6rem', cursor: 'pointer', fontSize: '0.85rem' }}
          >
            Log out
          </button>
        </span>
      )}
    </nav>
  )
}

function App() {
  const [account, setAccount] = useState<Account | null>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  })

  function handleLogin(data: Account) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    setAccount(data)
  }

  function handleLogout() {
    localStorage.removeItem(STORAGE_KEY)
    setAccount(null)
  }

  return (
    <BrowserRouter>
      <NavBar account={account} onLogout={handleLogout} />
      <Routes>
        <Route path="/"            element={<Home account={account} onLogin={handleLogin} />} />
        <Route path="/draft"       element={<Draft />} />
        <Route path="/roster"      element={<Roster account={account} />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
