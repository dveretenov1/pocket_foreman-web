'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { Button } from "@/app/components/ui/button"
import { Card } from "@/app/components/ui/card"
import { FileText, Plus, MessageSquarePlus } from 'lucide-react'
import { Loader2 } from 'lucide-react'
import FilesCard from '@/app/components/files/FilesCard'
import { api } from '@/app/services/api'
import type { APIFile } from '@/app/types'

export default function FilesPage() {
  const { user } = useAuth()
  const router = useRouter()
  const [files, setFiles] = useState<APIFile[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) {
      router.replace('/login')
      return
    }
    loadFiles()
  }, [user])

  const loadFiles = async () => {
    try {
      setIsLoading(true)
      const files = await api.getUserFiles(() => user!.getIdToken())
      setFiles(files)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = async (fileId: number) => {
    try {
      const chat = await api.createChatWithFile(fileId, () => user!.getIdToken())
      router.push(`/chat?id=${chat.id}`)
    } catch (error: any) {
      setError(error.message)
    }
  }

  const handleAddToLatest = async (fileId: number) => {
    try {
      const chat = await api.addFileToLatestChat(fileId, () => user!.getIdToken())
      router.push(`/chat?id=${chat.id}`)
    } catch (error: any) {
      setError(error.message)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Your Files</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {files.map((file) => (
          <FilesCard
            key={file.id}
            file={file}
            onNewChat={handleNewChat}
            onAddToLatest={handleAddToLatest}
          />
        ))}
      </div>
    </div>
  )
}