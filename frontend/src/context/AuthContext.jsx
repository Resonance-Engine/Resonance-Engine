import { createContext, useContext, useState } from 'react'

const AuthContext = createContext(null)

// Admin credentials (placeholder — will be replaced by Clerk roles)
const ADMIN_EMAILS = ['admin', 'reiyyan']

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState(null)

  const login = (email) => {
    const role = ADMIN_EMAILS.includes(email?.toLowerCase()) ? 'admin' : 'user'
    setUser({ email, role })
    setIsAuthenticated(true)
  }

  const logout = () => {
    setUser(null)
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
