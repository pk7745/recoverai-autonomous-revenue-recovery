import React, { createContext, useContext, useState, useEffect } from 'react'
import { UserProfile, UserRole } from '../types'
import { api } from '../services/api'

interface AuthContextType {
  user: UserProfile | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Purge any legacy persistent token from localStorage to guarantee fresh visit starts at login
  if (typeof window !== 'undefined') {
    localStorage.removeItem('recoverai_token')
  }

  const [user, setUser] = useState<UserProfile | null>(null)
  const [token, setToken] = useState<string | null>(typeof window !== 'undefined' ? sessionStorage.getItem('recoverai_token') : null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = sessionStorage.getItem('recoverai_token')
      if (storedToken) {
        try {
          const profile = await api.getMe()
          setUser(profile)
          setToken(storedToken)
        } catch {
          // Token expired or invalid
          sessionStorage.removeItem('recoverai_token')
          setUser(null)
          setToken(null)
        }
      }
      setIsLoading(false)
    }
    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    const res = await api.login(email, password)
    setUser(res.user)
    setToken(res.access_token)
  }

  const logout = () => {
    api.logout()
    setUser(null)
    setToken(null)
  }

  const isAdmin = user?.role === 'MERCHANT_ADMIN'

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
