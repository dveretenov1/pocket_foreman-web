// app/components/chat/ChatMessage.tsx
import { FileText, X } from 'lucide-react'
import { Button } from "@/app/components/ui/button"

interface FileAttachment {
  id: number
  original_name: string
  s3_key: string
}

interface Message {
  id: number
  chat_id: number
  content: string
  role: 'user' | 'assistant'
  created_at: string
  files?: FileAttachment[]
}

interface ChatMessageProps {
  message: Message
  activeFiles?: FileAttachment[]
  onRemoveFile?: (fileId: number) => void
}

import Image from 'next/image'

export default function ChatMessage({ message, activeFiles, onRemoveFile }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 items-start`}>
      {!isUser && (
        <Image
          src="/assets/ai-logo.svg"
          alt="AI"
          width={32}
          height={32}
          className="mr-2"
        />
      )}
      <div className={`max-w-[80%]`}>
        <div
          className={`rounded-lg p-3 ${
            isUser
              ? 'bg-purple-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    </div>
  )
}
