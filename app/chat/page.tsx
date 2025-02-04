'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { ScrollArea } from "@/app/components/ui/scroll-area"
import { Loader2 } from 'lucide-react'
import { Button } from "@/app/components/ui/button"
import ChatSidebar from '@/app/components/chat/ChatSidebar'
import ChatMessage from '@/app/components/chat/ChatMessage'
import ChatInput from '@/app/components/chat/ChatInput'
import ExpandedFilesSidebar from '@/app/components/chat/ExpandedFilesSidebar'
import ExpandedLibrarySidebar from '@/app/components/chat/ExpandedLibrarySidebar'
import { api } from '@/app/services/api'
import type { APIChat, APIMessage, APIFile } from '@/app/types'

interface StreamMessage {
  message_id?: number;
  content?: string;
  done?: boolean;
  error?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const DEFAULT_TITLE = "New Chat"

export default function ChatPage() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [chats, setChats] = useState<APIChat[]>([])
  const [selectedChat, setSelectedChat] = useState<APIChat | null>(null)
  const [messages, setMessages] = useState<APIMessage[]>([])
  const [streamingMessage, setStreamingMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [activeFiles, setActiveFiles] = useState<APIFile[]>([])
  const [showFiles, setShowFiles] = useState(false)
  const [showLibrary, setShowLibrary] = useState(false)
  const [allFiles, setAllFiles] = useState<APIFile[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user) {
      router.replace('/login')
      return
    }
    
    const initializeData = async () => {
      try {
        console.log('Starting data initialization...')
        setIsLoading(true)
        
        // Load chats and files in parallel
        const [chatList, fileList] = await Promise.all([
          api.getChats(() => user!.getIdToken()),
          api.getUserFiles(() => user!.getIdToken())
        ])
        
        console.log('Initial data loaded:', { chats: chatList.length, files: fileList.length })
        
        // Update states
        setChats(chatList)
        setAllFiles(fileList)
        
        // Handle chat selection
        const urlParams = new URLSearchParams(window.location.search)
        const chatId = urlParams.get('id')
        
        if (chatId) {
          const chat = chatList.find(c => c.id === parseInt(chatId))
          if (chat) {
            setSelectedChat(chat)
            // Load chat files
            const chatFiles = await api.get<APIFile[]>(`/chats/${chat.id}/files`, () => user!.getIdToken())
            setActiveFiles(Array.isArray(chatFiles) ? chatFiles : [])
            // Load messages
            const messages = await api.getChatMessages(chat.id, () => user!.getIdToken())
            setMessages(messages)
          }
        } else if (chatList.length > 0) {
          setSelectedChat(chatList[0])
          // Load chat files
          const chatFiles = await api.get<APIFile[]>(`/chats/${chatList[0].id}/files`, () => user!.getIdToken())
          setActiveFiles(Array.isArray(chatFiles) ? chatFiles : [])
          // Load messages
          const messages = await api.getChatMessages(chatList[0].id, () => user!.getIdToken())
          setMessages(messages)
        }
      } catch (error) {
        console.error('Error initializing data:', error)
        setError('Failed to load initial data')
      } finally {
        setIsLoading(false)
      }
    }

    initializeData()
  }, [user])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  useEffect(() => {
    if (!error) return
    const timer = setTimeout(() => setError(null), 5000)
    return () => clearTimeout(timer)
  }, [error])

  const loadAllFiles = async () => {
    try {
      console.log('Fetching user files...')
      const files = await api.getUserFiles(() => user!.getIdToken())
      console.log('Files fetched:', files)
      
      if (Array.isArray(files)) {
        setAllFiles(files)
        console.log('Files state updated:', files.length, 'files')
      } else {
        console.error('Received invalid files data:', files)
        setError('Invalid files data received')
      }
    } catch (error: any) {
      console.error('Error loading files:', error)
      setError(error.message || 'Failed to load files')
    }
  }

  const loadChatAndFiles = async (chatId: number) => {
    try {
      setIsLoading(true)
      setError(null) // Clear any previous errors
      
      // Load messages, chat files, and refresh all files in parallel
      const [messages, chatFiles, allUserFiles] = await Promise.all([
        api.getChatMessages(chatId, () => user!.getIdToken()),
        api.get<APIFile[]>(`/chats/${chatId}/files`, () => user!.getIdToken()),
        api.getUserFiles(() => user!.getIdToken())
      ])

      // Always update states when loading a chat
      setMessages(messages)
      setActiveFiles(Array.isArray(chatFiles) ? chatFiles : []) // Ensure files is an array
      setAllFiles(allUserFiles) // Update all files list

      // Log state updates for debugging
      console.log('Chat data loaded:', {
        chatId,
        messageCount: messages.length,
        chatFileCount: Array.isArray(chatFiles) ? chatFiles.length : 0,
        allFileCount: Array.isArray(allUserFiles) ? allUserFiles.length : 0
      })
    } catch (error: any) {
      console.error('Error loading chat and files:', error)
      setError(error.message || 'Failed to load chat data')
      setMessages([])
      setActiveFiles([])
    } finally {
      setIsLoading(false)
    }
  }

  const loadChats = async () => {
    try {
      console.log('Fetching chats...')
      const chatList = await api.getChats(() => user!.getIdToken())
      console.log('Chats fetched:', chatList)
      setChats(chatList)
      
      const urlParams = new URLSearchParams(window.location.search)
      const chatId = urlParams.get('id')
      
      if (chatId) {
        const chat = chatList.find(c => c.id === parseInt(chatId))
        if (chat) {
          setSelectedChat(chat)
          await loadChatAndFiles(chat.id)
        }
      } else if (chats.length > 0) {
        setSelectedChat(chats[0])
        await loadChatAndFiles(chats[0].id)
      }
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateChat = async () => {
    try {
      setError(null)
      const newChat = await api.createChat(DEFAULT_TITLE, () => user!.getIdToken())
      setChats(prevChats => [newChat, ...prevChats])
      setSelectedChat(newChat)
      setMessages([])
      setActiveFiles([])
      
      // Update URL with new chat ID
      window.history.pushState({}, '', `/chat?id=${newChat.id}`)
    } catch (error: any) {
      console.error('Error creating chat:', error)
      setError(error.message || 'Failed to create new chat')
    }
  }

  const handleSendMessage = async (content: string, fileIds: number[]) => {
    if (!selectedChat) return
    if (!content.trim()) {
      setError('Message cannot be empty')
      return
    }
    
    try {
      setIsSending(true)
      setStreamingMessage('')

      const userMessage: APIMessage = {
        id: Date.now(),
        chat_id: selectedChat.id,
        content: content.trim(),
        role: 'user',
        created_at: new Date().toISOString(),
        files: activeFiles.filter(f => fileIds.includes(f.id))
      }
      setMessages(prev => [...prev, userMessage])

      const response = await api.sendMessage(
        selectedChat.id, 
        content.trim(),
        fileIds, 
        () => user!.getIdToken()
      )

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response reader')

      let assistantMessage: APIMessage | null = null
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += new TextDecoder().decode(value)
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.error) {
                throw new Error(data.error)
              }

              if (!assistantMessage && data.message_id) {
                assistantMessage = {
                  id: data.message_id,
                  chat_id: selectedChat.id,
                  content: data.content || '',
                  role: 'assistant',
                  created_at: new Date().toISOString(),
                  files: activeFiles
                }
                setMessages(prev => [...prev, assistantMessage!])

                if (selectedChat.title === DEFAULT_TITLE) {
                  const newTitle = data.content?.slice(0, 25) + (data.content?.length > 25 ? '...' : '') || DEFAULT_TITLE
                  try {
                    const updatedChat = await api.updateChatTitle(selectedChat.id, newTitle, () => user!.getIdToken())
                    setChats(prevChats => prevChats.map(chat => 
                      chat.id === selectedChat.id ? { ...chat, title: newTitle } : chat
                    ))
                    setSelectedChat(prev => prev ? { ...prev, title: newTitle } : prev)
                  } catch (error: any) {
                    console.error('Failed to update chat title:', error)
                  }
                }
              } else if (assistantMessage && data.content) {
                assistantMessage.content += data.content
                setMessages(prev => 
                  prev.map(msg => 
                    msg.id === assistantMessage!.id 
                      ? { ...msg, content: assistantMessage!.content }
                      : msg
                  )
                )
              }
            } catch (error) {
              console.error('Error parsing SSE data:', error)
              throw error
            }
          }
        }
      }
    } catch (error: any) {
      setError(error.message || 'Failed to send message')
    } finally {
      setIsSending(false)
    }
  }

  const handleLogout = async () => {
    try {
      await logout()
      router.push('/login')
    } catch (error: any) {
      setError('Failed to logout')
    }
  }

  const handleRemoveFile = async (fileId: number) => {
    if (!selectedChat) return
    try {
      await api.removeFileFromChat(fileId, selectedChat.id, () => user!.getIdToken())
      setActiveFiles(prev => prev.filter(f => f.id !== fileId))
      // Refresh all files after removal
      const allUserFiles = await api.getUserFiles(() => user!.getIdToken())
      setAllFiles(allUserFiles)
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
    <div className="flex h-screen bg-gray-100 chat-layout">
      <ChatSidebar
        chats={chats.map(chat => ({
          ...chat,
          updated_at: chat.created_at
        }))}
        selectedChat={selectedChat && { ...selectedChat, updated_at: selectedChat.created_at }}
        onSelectChat={async (chat) => {
          setSelectedChat({
            ...chat,
            user_id: selectedChat?.user_id ?? user?.uid ?? '',
            message_count: selectedChat?.message_count ?? 0,
            last_message_at: (selectedChat?.last_message_at ?? chat.created_at).toString()
          })
          await loadChatAndFiles(chat.id)
        }}
        onCreateChat={handleCreateChat}
        onLogout={handleLogout}
        onToggleFiles={() => {
          setShowFiles(!showFiles)
          setShowLibrary(false)
        }}
        onToggleLibrary={() => {
          setShowLibrary(!showLibrary)
          setShowFiles(false)
        }}
        showFiles={showFiles}
        showLibrary={showLibrary}
      />

      {showFiles && (
        <ExpandedFilesSidebar
          files={allFiles}
          onClose={() => setShowFiles(false)}
          onNewChat={async (fileId) => {
            try {
              const chat = await api.createChatWithFile(fileId, () => user!.getIdToken())
              setChats(prevChats => [chat, ...prevChats])
              setSelectedChat(chat)
              await loadChatAndFiles(chat.id)
              setShowFiles(false)
            } catch (error: any) {
              setError(error.message || 'Failed to create chat with file')
            }
          }}
          onAddToLatest={async (fileId) => {
            if (!selectedChat) return
            try {
              await api.addFileToLatestChat(fileId, () => user!.getIdToken())
              
              // Refresh both active files and all files
              const [chatFiles, allUserFiles] = await Promise.all([
                api.get<APIFile[]>(`/chats/${selectedChat.id}/files`, () => user!.getIdToken()),
                api.getUserFiles(() => user!.getIdToken())
              ])
              
              // Update states with new data
              setActiveFiles(Array.isArray(chatFiles) ? chatFiles : [])
              setAllFiles(allUserFiles)
              
              // Close files sidebar
              setShowFiles(false)
            } catch (error: any) {
              setError(error.message || 'Failed to add file to chat')
            }
          }}
        />
      )}

      {showLibrary && (
        <ExpandedLibrarySidebar
          chats={chats}
          selectedChat={selectedChat}
          onClose={() => setShowLibrary(false)}
          onSelectChat={async (chat) => {
            setSelectedChat(chat)
            await loadChatAndFiles(chat.id)
            setShowLibrary(false)
          }}
        />
      )}

      <div className={`flex-1 flex flex-col chat-content ${
        showFiles || showLibrary ? 'ml-96' : 'ml-16'
      }`}>
        {selectedChat ? (
          <>
            <div className="bg-white p-4 shadow-sm">
              <h1 className="text-xl font-semibold">
                {selectedChat.title || DEFAULT_TITLE}
              </h1>
            </div>

            <ScrollArea className="flex-1 p-4 relative">
              <div className="space-y-4">
                {messages.map((message) => (
                  <ChatMessage 
                    key={message.id} 
                    message={message}
                    activeFiles={activeFiles}
                    onRemoveFile={handleRemoveFile}
                  />
                ))}
                {streamingMessage && (
                  <ChatMessage
                    message={{
                      id: -1,
                      chat_id: selectedChat.id,
                      content: streamingMessage,
                      role: 'assistant',
                      created_at: new Date().toISOString()
                    }}
                    activeFiles={activeFiles}
                    onRemoveFile={handleRemoveFile}
                  />
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            <ChatInput
              onSendMessage={handleSendMessage}
              onRemoveFile={handleRemoveFile}
              disabled={isSending}
              chatId={selectedChat.id}
              activeFiles={activeFiles}
              setActiveFiles={setActiveFiles}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-xl font-semibold mb-2">No chat selected</h2>
              <Button onClick={handleCreateChat}>Start a new chat</Button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg z-50 animate-in fade-in slide-in-from-bottom-5">
          {error}
        </div>
      )}
    </div>
  )
}
