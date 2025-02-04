// app/components/chat/ChatInput.tsx
'use client'

import { useState, useRef, Dispatch, SetStateAction } from 'react'
import { useAuth } from '@/app/contexts/AuthContext'
import { Button } from "@/app/components/ui/button"
import { Textarea } from "@/app/components/ui/textarea"
import { Card, CardContent } from "@/app/components/ui/card"
import { Paperclip, Loader2 } from 'lucide-react'
import { FileAttachmentPreview } from './FileAttachmentPreview'
import type { APIFile } from '@/app/types'

import { api } from '@/app/services/api'

interface ChatInputProps {
  onSendMessage: (content: string, fileIds: number[]) => Promise<void>
  onRemoveFile: (fileId: number) => Promise<void>
  disabled: boolean
  chatId: number
  activeFiles: APIFile[]
  setActiveFiles: Dispatch<SetStateAction<APIFile[]>>
}

interface FileAttachment {
  id: number
  original_name: string
  s3_key: string
}

export default function ChatInput({ onSendMessage, onRemoveFile, disabled, chatId, activeFiles, setActiveFiles }: ChatInputProps) {
  const { user } = useAuth()
  const [message, setMessage] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!chatId || !event.target.files?.length) return

    const file = event.target.files[0]
    if (!file) return

    try {
      setIsUploading(true)

      const newFile = await api.uploadFile(file, () => user!.getIdToken())

      setActiveFiles(prev => [...prev, newFile])

    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const removeFile = async (fileId: number) => {
    await onRemoveFile(fileId)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim() || disabled) return
  
    const fileIds = activeFiles.map(file => file.id)
    await onSendMessage(message, fileIds)
    setMessage('')
    // Don't clear activeFiles - they should persist
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="p-4 bg-white border-t">
      <Card className="rounded-lg">
        <CardContent className="p-2">
          <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
            <FileAttachmentPreview 
              files={activeFiles}
              onRemove={removeFile}
              disabled={disabled}
            />
            <div className="relative">
              <Textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                className="flex-1 min-h-[40px] max-h-[200px] pr-24"
                disabled={disabled}
              />
              <div className="absolute right-2 bottom-2 flex space-x-2">
                <Button 
                  type="button" 
                  variant="ghost" 
                  className="rounded-full h-8 w-8 p-0 flex items-center justify-center"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={disabled || isUploading}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                    accept=".pdf,.txt,.csv"
                  />
                  {isUploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Paperclip className="h-4 w-4" />
                  )}
                </Button>
                <Button 
                  type="submit" 
                  disabled={!message.trim() || disabled}
                  className="bg-purple-600 hover:bg-purple-700 text-white h-8 px-3 py-1"
                >
                  {disabled ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    'Send'
                  )}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
