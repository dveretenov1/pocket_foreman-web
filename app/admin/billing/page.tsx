'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { Card, CardHeader, CardTitle, CardContent } from "@/app/components/ui/card"
import { Input } from "@/app/components/ui/input"
import { Button } from "@/app/components/ui/button"
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Search, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

interface UserBilling {
  id: string
  email: string
  subscription: {
    tier: string
    price_usd: number
    monthly_pft: number
  }
  usage: {
    total_pft: number
    overage_cost_usd: number
  }
}

export default function AdminBillingPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [users, setUsers] = useState<UserBilling[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) {
      router.replace('/login')
      return
    }
    loadUsers()
  }, [user])

  const loadUsers = async () => {
    try {
      const token = await user!.getIdToken()
      const response = await fetch(`${API_URL}/api/billing/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('Not authorized to access admin features')
        }
        throw new Error('Failed to fetch users')
      }
      
      const data = await response.json()
      setUsers(data)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGrantTokens = async (userId: string, amount: number) => {
    try {
      const token = await user!.getIdToken()
      const response = await fetch(`${API_URL}/api/billing/admin/users/${userId}/grant`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ amount })
      })
      
      if (!response.ok) throw new Error('Failed to grant tokens')
      
      // Refresh user data
      await loadUsers()
    } catch (error: any) {
      setError(error.message)
    }
  }

  const filteredUsers = users.filter(user => 
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-red-500">
        Error: {error}
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>User Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
            <Input
              type="text"
              placeholder="Search users..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          <ScrollArea className="h-[600px]">
            <div className="space-y-4">
              {filteredUsers.map((user) => (
                <Card key={user.id}>
                  <CardContent className="p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{user.email}</p>
                        <p className="text-sm text-muted-foreground">
                          Plan: {user.subscription.tier} (${user.subscription.price_usd}/mo)
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Usage: {user.usage.total_pft.toLocaleString()} PFT
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          onClick={() => handleGrantTokens(user.id, 1000)}
                        >
                          Grant 1,000 PFT
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleGrantTokens(user.id, 5000)}
                        >
                          Grant 5,000 PFT
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}