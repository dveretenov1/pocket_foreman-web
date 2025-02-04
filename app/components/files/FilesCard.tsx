import { Button } from "@/app/components/ui/button"
import { Card } from "@/app/components/ui/card"
import { FileText, Plus, MessageSquarePlus } from 'lucide-react'
import type { APIFile } from '@/app/types'

interface FilesCardProps {
  file: APIFile
  onNewChat: (fileId: number) => Promise<void>
  onAddToLatest: (fileId: number) => Promise<void>
}

export default function FilesCard({ file, onNewChat, onAddToLatest }: FilesCardProps) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="h-5 w-5" />
        <span className="font-medium truncate">{file.original_name}</span>
      </div>
      <div className="flex gap-2 mt-4">
        <Button 
          variant="default" 
          className="flex-1"
          onClick={() => onNewChat(file.id)}
        >
          <Plus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
        <Button 
          variant="secondary" 
          className="flex-1"
          onClick={() => onAddToLatest(file.id)}
        >
          <MessageSquarePlus className="h-4 w-4 mr-2" />
          Add to Latest
        </Button>
      </div>
    </Card>
  )
}