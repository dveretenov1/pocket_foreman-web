// app/components/chat/ChatSidebar.tsx
'use client'

import { useAuth } from '@/app/contexts/AuthContext'
import { Button } from "@/app/components/ui/button"
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Plus, LogOut, Files, BookOpen, CreditCard, Settings, X } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'

interface Chat {
  id: number
  title: string
  created_at: string
  updated_at: string
}

interface ChatSidebarProps {
  chats: Chat[]
  selectedChat: Chat | null
  onSelectChat: (chat: Chat) => void
  onCreateChat: () => void
  onLogout: () => Promise<void>
  isAdmin?: boolean
  onToggleFiles: () => void
  onToggleLibrary: () => void
  showFiles: boolean
  showLibrary: boolean
}

export default function ChatSidebar({
  chats,
  selectedChat,
  onSelectChat,
  onCreateChat,
  onLogout,
  isAdmin = false,
  onToggleFiles,
  onToggleLibrary,
  showFiles,
  showLibrary
}: ChatSidebarProps) {
  const { user } = useAuth()

  return (
    <aside className="w-16 h-full bg-white border-r flex flex-col items-center py-4 fixed left-0 top-0 z-10">
      <Link href="/chat" className="mb-6">
        <Image 
          src="/assets/logo.svg"
          alt="PocketForeman"
          width={32}
          height={32}
          className="hover:opacity-80 transition-opacity"
        />
      </Link>

      <div className="flex flex-col items-center space-y-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCreateChat}
          className="rounded-full hover:bg-purple-100"
        >
          <Plus className="h-5 w-5 text-purple-600" />
        </Button>

        <Button
          variant={showFiles ? "default" : "ghost"}
          size="sm"
          onClick={onToggleFiles}
          className={`rounded-full ${showFiles ? 'bg-purple-100 text-purple-600' : 'hover:bg-purple-100'}`}
        >
          <Files className="h-5 w-5" />
        </Button>

        <Button
          variant={showLibrary ? "default" : "ghost"}
          size="sm"
          onClick={onToggleLibrary}
          className={`rounded-full ${showLibrary ? 'bg-purple-100 text-purple-600' : 'hover:bg-purple-100'}`}
        >
          <BookOpen className="h-5 w-5" />
        </Button>

        <div className="flex-1"></div>

        <Link href="/billing">
          <Button
            variant="ghost"
            size="sm"
            className="rounded-full hover:bg-purple-100"
          >
            <CreditCard className="h-5 w-5" />
          </Button>
        </Link>

        {isAdmin && (
          <Link href="/admin/billing">
            <Button
              variant="ghost"
              size="sm"
              className="rounded-full hover:bg-purple-100"
            >
              <Settings className="h-5 w-5" />
            </Button>
          </Link>
        )}
      </div>

      <div className="mt-auto">
        <Button
          onClick={onLogout}
          variant="ghost"
          size="sm"
          className="rounded-full hover:bg-purple-100"
        >
          <LogOut className="h-5 w-5" />
        </Button>
      </div>
    </aside>
  )
}
