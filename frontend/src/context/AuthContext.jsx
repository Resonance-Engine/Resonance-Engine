import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, logout as apiLogout, isLoggedIn } from '../api/client'

const AuthContext = createContext(null)

// Admin credentials (placeholder — will be replaced by Clerk roles)
const ADMIN_EMAILS = ['admin', 'reiyyan']

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(isLoggedIn())
  const [operator, setOperator] = useState(null)
  const [user, setUser] = useState(null)

  // Sync auth state if token exists on mount
  useEffect(() => {
    if (isLoggedIn()) {
      setIsAuthenticated(true)
    }
  }, [])

  const login = async (username, password) => {
    const data = await apiLogin(username, password)
    const role = ADMIN_EMAILS.includes(username?.toLowerCase()) ? 'admin' : 'user'
    setIsAuthenticated(true)
    setOperator(data.operator)
    setUser({ email: username, role })
    return data
  }

  const logout = () => {
    apiLogout()
    setIsAuthenticated(false)
    setOperator(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, operator, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
