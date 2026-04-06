import { createContext, useContext, useState, useEffect } from 'react'
import { login as apiLogin, logout as apiLogout, isLoggedIn } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(isLoggedIn())
  const [operator, setOperator] = useState(null)

  // Sync auth state if token exists on mount
  useEffect(() => {
    if (isLoggedIn()) {
      setIsAuthenticated(true)
    }
  }, [])

  const login = async (username, password) => {
    const data = await apiLogin(username, password)
    setIsAuthenticated(true)
    setOperator(data.operator)
    return data
  }

  const logout = () => {
    apiLogout()
    setIsAuthenticated(false)
    setOperator(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, operator, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
