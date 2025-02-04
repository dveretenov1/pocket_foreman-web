// app/components/chat/FileAttachmentPreview.tsx
import { X, FileText } from 'lucide-react'
import { Button } from "@/app/components/ui/button"

interface FileAttachment {
  id: number
  original_name: string
  s3_key: string
}

interface FileAttachmentPreviewProps {
  files: FileAttachment[]
  onRemove: (id: number) => void
  disabled?: boolean
}

export function FileAttachmentPreview({ files, onRemove, disabled }: FileAttachmentPreviewProps) {
  if (files.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2">
      {files.map((file) => (
        <div
          key={file.id}
          className="flex items-center gap-2 bg-gray-50 p-2 rounded-md border border-gray-200"
        >
          <FileText className="h-4 w-4" />
          <span className="text-sm truncate max-w-[200px]">
            {file.original_name}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0"
            onClick={() => onRemove(file.id)}
            disabled={disabled}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  )
}
