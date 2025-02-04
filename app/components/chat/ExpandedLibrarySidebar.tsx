'use client'

import { useState } from 'react'
import { Button } from "@/app/components/ui/button"
import { Card } from "@/app/components/ui/card"
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Search, MessageSquare, X } from 'lucide-react'
import { Input } from "@/app/components/ui/input"
import type { APIChat } from '@/app/types'

interface ExpandedLibrarySidebarProps {
  chats: APIChat[]
  selectedChat: APIChat | null
  onClose: () => void
  onSelectChat: (chat: APIChat) => void
}

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

export default function ExpandedLibrarySidebar({
  chats,
  selectedChat,
  onClose,
  onSelectChat
}: ExpandedLibrarySidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')

  const filteredChats = chats.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="w-80 h-full bg-white border-r fixed left-16 top-0 animate-slide-right">
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold">Library</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="rounded-full hover:bg-gray-100"
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 h-4 w-4" />
          <Input
            type="text"
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <ScrollArea className="h-[calc(100vh-8rem)] px-4">
        <div className="space-y-3">
          {filteredChats.map((chat) => (
            <Card 
              key={chat.id} 
              className={`p-3 cursor-pointer transition-colors ${
                selectedChat?.id === chat.id ? 'bg-purple-50 border-purple-200' : 'hover:bg-gray-50'
              }`}
              onClick={() => onSelectChat(chat)}
            >
              <div className="flex items-start space-x-3">
                <MessageSquare className={`h-5 w-5 mt-1 ${
                  selectedChat?.id === chat.id ? 'text-purple-600' : 'text-gray-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium truncate">{chat.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatTimestamp(chat.updated_at || chat.created_at)}
                  </p>
                  {chat.message_count && (
                    <p className="text-xs text-gray-500 mt-1">
                      {chat.message_count} messages
                    </p>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
