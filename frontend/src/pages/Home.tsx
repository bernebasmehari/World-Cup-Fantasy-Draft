import { useState } from 'react'

// describes the shape of the form data — like a Java interface
interface JoinForm {
  name: string
  room_code: string
}

function Home() {
  // useState holds the form values in memory
  // starts as empty strings, updates as the user types
  const [form, setForm] = useState<JoinForm>({ name: '', room_code: '' })

  // called when the user clicks Join
  // sends a POST request to the backend with the form data
  function handleJoin() {
    fetch('http://localhost:8000/users', {
      method: 'POST',                                    // tells the server we're creating something
      headers: { 'Content-Type': 'application/json' },  // tells the server we're sending JSON
      body: JSON.stringify(form)                         // converts the form object to a JSON string
    })
      .then(res => res.json())                           // parse the response as JSON
      .then(data => console.log('User created:', data))  // log the new user object
  }

  return (
    <div>
      <h1>WorldDraft</h1>

      {/* controlled input — React controls the value, updates state on every keystroke */}
      <input
        placeholder="Your name"
        value={form.name}
        onChange={e => setForm({ ...form, name: e.target.value })}
      />

      {/* ...form spreads the existing form values so we don't overwrite the other field */}
      <input
        placeholder="Room code"
        value={form.room_code}
        onChange={e => setForm({ ...form, room_code: e.target.value })}
      />

      <button onClick={handleJoin}>Join Draft</button>
    </div>
  )
}

export default Home