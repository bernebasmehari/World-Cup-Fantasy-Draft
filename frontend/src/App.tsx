import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
// importing each page component we created
import Home from './pages/Home'
import Draft from './pages/Draft'
import Roster from './pages/Roster'
import Leaderboard from './pages/Leaderboard'

function App() {
  return (
    // BrowserRouter watches the URL bar and decides what to render
    // everything inside here has access to routing
    <BrowserRouter>

      {/* nav bar sits outside Routes so it shows on every page */}
      <nav>
        {/* Link is like an <a> tag but it doesn't reload the page */}
        {/* it just swaps out the component — much faster */}
        <Link to="/">Home</Link> |{' '}
        <Link to="/draft">Draft</Link> |{' '}
        <Link to="/roster">Roster</Link> |{' '}
        <Link to="/leaderboard">Leaderboard</Link>
      </nav>

      {/* Routes looks at the current URL and renders the matching Route */}
      {/* only one Route renders at a time */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/draft" element={<Draft />} />
        <Route path="/roster" element={<Roster />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
      </Routes>

    </BrowserRouter>
  )
}

export default App