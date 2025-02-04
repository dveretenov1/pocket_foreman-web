'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { Input } from "@/app/components/ui/input"
import { Card } from "@/app/components/ui/card"
import { Search, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/app/services/api'
import type { APIChat, APIMessage } from '@/app/types'

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffInMs = now.getTime() - date.getTime()
  const diffInMinutes = Math.floor(diffInMs / 60000)
  const diffInHours = Math.floor(diffInMs / 3600000)
  const diffInDays = Math.floor(diffInMs / 86400000)

  if (diffInMinutes < 1) {
    return 'just now'
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes} ${diffInMinutes === 1 ? 'minute' : 'minutes'} ago`
  } else if (diffInHours < 24) {
    return `${diffInHours} ${diffInHours === 1 ? 'hour' : 'hours'} ago`
  } else if (diffInDays < 2) {
    return 'yesterday'
  } else {
    return date.toLocaleDateString()
  }
}

function getFirstAssistantMessage(messages: APIMessage[]): string {
  const assistantMessage = messages.find(m => m.role === 'assistant')
  if (!assistantMessage) return 'No response yet'
  return assistantMessage.content
}

export default function LibraryPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState('')
  const [chats, setChats] = useState<APIChat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [forceUpdate, setForceUpdate] = useState(0)  // Added to force timestamp updates

  useEffect(() => {
    if (!user) {
      router.replace('/login')
      return
    }
    loadChats()
  }, [user])

  // Add effect to update timestamps every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setForceUpdate(prev => prev + 1)
    }, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [])

  const loadChats = async () => {
    try {
      setIsLoading(true)
      const allChats = await api.getChats(() => user!.getIdToken())
      
      // Load messages for each chat
      const chatsWithMessages = await Promise.all(
        allChats.map(async (chat: APIChat) => {
          const messages = await api.getChatMessages(chat.id, () => user!.getIdToken())
          return { ...chat, messages }
        })
      )
      
      setChats(chatsWithMessages)
    } catch (error) {
      console.error('Failed to load chats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredChats = chats.filter(chat => {
    const searchLower = searchQuery.toLowerCase()
    const assistantMessage = getFirstAssistantMessage(chat.messages || [])
    return (
      chat.title.toLowerCase().includes(searchLower) ||
      assistantMessage.toLowerCase().includes(searchLower)
    )
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="fixed top-4 left-4 z-10">
        <Link href="/chat" className="text-2xl font-bold text-gray-900 hover:text-gray-700 transition-colors">
          <h1>PocketForeman</h1>
        </Link>
      </div>

      <main className="max-w-3xl mx-auto p-6 pt-16">
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
          <Input
            type="text"
            placeholder="Search your chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 w-full"
          />
        </div>

        <div className="text-sm text-gray-600 mb-4">
          You have {chats.length} previous chats with Claude
        </div>

        <div className="space-y-3">
          {filteredChats.map((chat) => {
            const assistantMessage = getFirstAssistantMessage(chat.messages || [])
            const preview = assistantMessage.length > 50 
              ? assistantMessage.substring(0, 50) + '...'
              : assistantMessage

            return (
              <Link key={chat.id} href={`/chat?id=${chat.id}`}>
                <Card className="p-4 hover:bg-gray-50 cursor-pointer transition-colors">
                  <h3 className="text-lg font-medium text-gray-900 mb-1">
                    {chat.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">
                    {preview}
                  </p>
                  <p className="text-xs text-gray-500">
                    Last accessed {formatTimestamp(chat.updated_at || chat.created_at)}
                  </p>
                </Card>
              </Link>
            )
          })}
        </div>
      </main>
    </div>
  )
}