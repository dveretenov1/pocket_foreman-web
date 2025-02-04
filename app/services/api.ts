import axios from 'axios'
import type { APIChat, APIMessage, APIFile } from '@/app/types'

const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
}, (error) => {
  return Promise.reject(error)
})

export const api = {
  // Chat endpoints
  getChats: async (getToken: () => Promise<string>): Promise<APIChat[]> => {
    const token = await getToken()
    const response = await axiosInstance.get<APIChat[]>('/chats', {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  createChat: async (title: string, getToken: () => Promise<string>): Promise<APIChat> => {
    const token = await getToken()
    const response = await axiosInstance.post<APIChat>('/chats', { title }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  getChatMessages: async (chatId: number, getToken: () => Promise<string>): Promise<APIMessage[]> => {
    const token = await getToken()
    const response = await axiosInstance.get<APIMessage[]>(`/chats/${chatId}/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  sendMessage: async (chatId: number, content: string, fileIds: number[], getToken: () => Promise<string>): Promise<Response> => {
    const token = await getToken()
    const response = await fetch(`${baseURL}/chats/${chatId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content, file_ids: fileIds }),
    })
    if (!response.ok) {
      throw new Error('Failed to send message')
    }
    return response
  },

  updateChatTitle: async (chatId: number, title: string, getToken: () => Promise<string>): Promise<APIChat> => {
    const token = await getToken()
    const response = await axiosInstance.put<APIChat>(`/chats/${chatId}/title`, { title }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  // File endpoints
  uploadFile: async (file: File, getToken: () => Promise<string>): Promise<APIFile> => {
    const token = await getToken()
    const formData = new FormData()
    formData.append('file', file)
    const response = await axiosInstance.post<APIFile>('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`
      }
    })
    return response.data
  },

  // Add file to chat
  addFileToChat: async (chatId: number, fileId: number, getToken: () => Promise<string>): Promise<void> => {
    const token = await getToken()
    await axiosInstance.post(`/chats/${chatId}/files`, { file_ids: [fileId] }, {
      headers: { Authorization: `Bearer ${token}` }
    })
  },

  removeFileFromChat: async (fileId: number, chatId: number, getToken: () => Promise<string>): Promise<void> => {
    const token = await getToken()
    await axiosInstance.delete(`/chats/${chatId}/files/${fileId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
  },

  addFileToLatestChat: async (fileId: number, getToken: () => Promise<string>): Promise<APIChat> => {
    const token = await getToken()
    const response = await axiosInstance.post<APIChat>('/chats/latest/files', { file_ids: [fileId] }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  // Generic HTTP methods for billing
  get: async <T>(path: string, getToken: () => Promise<string>): Promise<T> => {
    const token = await getToken()
    const response = await axiosInstance.get<T>(path, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  post: async <T>(path: string, data: any, getToken: () => Promise<string>): Promise<T> => {
    const token = await getToken()
    const response = await axiosInstance.post<T>(path, data, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  delete: async <T>(path: string, getToken: () => Promise<string>): Promise<T> => {
    const token = await getToken()
    const response = await axiosInstance.delete<T>(path, {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  // Get user's files
  getUserFiles: async (getToken: () => Promise<string>): Promise<APIFile[]> => {
    const token = await getToken()
    const response = await axiosInstance.get<APIFile[]>('/files', {
      headers: { Authorization: `Bearer ${token}` }
    })
    return response.data
  },

  // Create a new chat with a file
  createChatWithFile: async (fileId: number, getToken: () => Promise<string>): Promise<APIChat> => {
    const token = await getToken()
    // First create a new chat
    const chat = await api.createChat('New Chat', getToken)
    // Then add the file to it
    await api.addFileToChat(chat.id, fileId, getToken)
    return chat
  }
}
