const TOKEN_KEY = 'access_token'
const ROLE_KEY = 'role'

export function isAuthenticated() {
  return !!localStorage.getItem(TOKEN_KEY)
}

export function getRole() {
  return localStorage.getItem(ROLE_KEY)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export async function login(username, password) {
  const form = new URLSearchParams({ username, password })
  const res = await fetch('/api/v1/auth/login', { method: 'POST', body: form })
  if (!res.ok) throw new Error('Invalid credentials')
  const data = await res.json()
  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(ROLE', data.role)
  localStorage.setItem('username', data.username)
  return data
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem('username')
}

export async function authFetch(path, options = {}) {
  const token = getToken()
  const res = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  })
  if (res.status === 401) { logout(); window.location.href = '/login' }
  return res
}
