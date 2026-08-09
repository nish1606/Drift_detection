import { useState } from 'react'
import { login } from '../mockApi'

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await login(username, password)
      onLogin?.()
    } catch (err) {
      console.error('Login failed:', err)
      setError(err.message || 'Invalid credentials')
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-100">
      <form onSubmit={submit} className="bg-white p-8 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">Fraud Governance</h1>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <input className="w-full border p-2 mb-4 rounded" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
        <input className="w-full border p-2 mb-4 rounded" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="w-full bg-blue-600 text-white p-2 rounded" type="submit">Sign In</button>
      </form>
    </div>
  )
}
