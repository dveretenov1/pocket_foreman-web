'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/app/components/ui/button"
import { Card } from "@/app/components/ui/card"
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Search, FileText, X, ArrowRight, Plus } from 'lucide-react'
import { Input } from "@/app/components/ui/input"
import type { APIFile } from '@/app/types'

interface ExpandedFilesSidebarProps {
  files: APIFile[]
  onClose: () => void
  onNewChat: (fileId: number) => void
  onAddToLatest: (fileId: number) => void
}

export default function ExpandedFilesSidebar({
  files,
  onClose,
  onNewChat,
  onAddToLatest
}: ExpandedFilesSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  
  // Log files prop when it changes
  useEffect(() => {
    console.log('ExpandedFilesSidebar files:', files)
  }, [files])

  const filteredFiles = files?.filter(file =>
    file.original_name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  return (
    <div className="w-80 h-full bg-white border-r fixed left-16 top-0 z-0 animate-slide-right overflow-hidden">
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="text-lg font-semibold">Files</h2>
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
            placeholder="Search files..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      <ScrollArea className="h-[calc(100vh-8rem)] px-4 overflow-y-auto">
        <div className="space-y-3 pb-4">
          {filteredFiles.length === 0 ? (
            <div className="text-center text-gray-500 py-4">
              {files?.length === 0 ? 'No files uploaded yet' : 'No files match your search'}
            </div>
          ) : (
            filteredFiles.map((file) => (
            <Card key={file.id} className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <FileText className="h-5 w-5 text-purple-600 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-medium truncate">{file.original_name}</h3>
                    <p className="text-xs text-gray-500">
                      {file.created_at ? new Date(file.created_at).toLocaleDateString() : 'No date'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-2 flex-shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => onNewChat(file.id)}
                    title="Create new chat"
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => onAddToLatest(file.id)}
                    title="Add to current chat"
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          )))}
        </div>
      </ScrollArea>
    </div>
  )
}
