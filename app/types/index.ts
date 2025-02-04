// app/types/index.ts

// User related types
export type SubscriptionTier = 'free' | 'pro' | 'enterprise';

export interface UserUsage {
  tokenCount: number;
  costTotal: number;
}

export interface User {
  uid: string;
  email: string;
  displayName?: string;
  subscription: SubscriptionTier;
  createdAt: Date;
  updatedAt?: Date;
  usage: UserUsage;
  settings?: UserSettings;
  deleted?: boolean;
  deletedAt?: Date;
}

export interface UserSettings {
  theme?: 'light' | 'dark' | 'system';
  notifications?: boolean;
  language?: string;
}

// Chat related types
export interface APIChat {
  id: number;
  user_id: string;
  title: string;
  created_at: string;
  updated_at?: string;
  message_count?: number;
  last_message_at: string | null;
  messages?: APIMessage[];
  deleted?: boolean;
  deleted_at?: string;
}

export interface APIMessage {
  id: number;
  chat_id: number;
  content: string;
  role: 'user' | 'assistant';
  created_at: string;
  files?: APIFile[];
  deleted?: boolean;
  deleted_at?: string;
}

export interface APIFile {
  id: number;
  original_name: string;
  s3_key: string;
  user_id?: string;
  created_at?: string;
  deleted?: boolean;
  deleted_at?: string;
}

// Project related types
export interface Project {
  id: string;
  userId: string;
  name: string;
  description?: string;
  createdAt: Date;
  updatedAt: Date;
  deleted?: boolean;
  deletedAt?: Date;
  members?: ProjectMember[];
  settings?: ProjectSettings;
}

export interface ProjectMember {
  userId: string;
  role: 'owner' | 'editor' | 'viewer';
  joinedAt: Date;
}

export interface ProjectSettings {
  visibility: 'private' | 'team' | 'public';
  allowComments: boolean;
  allowSharing: boolean;
}

// Document related types
export interface Document {
  id: string;
  userId: string;
  projectId?: string;
  filename: string;
  fileSize: number;
  mimeType: string;
  s3Key: string;
  createdAt: Date;
  updatedAt?: Date;
  deleted?: boolean;
  deletedAt?: Date;
  metadata?: DocumentMetadata;
}

export interface DocumentMetadata {
  description?: string;
  tags?: string[];
  thumbnailUrl?: string;
  processing?: {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    error?: string;
    progress?: number;
  };
}

// API related types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ChatAPIResponse extends APIResponse {
  data?: {
    content: string;
    usage?: {
      promptTokens: number;
      completionTokens: number;
      totalTokens: number;
      cost: number;
    };
  };
}

// Error types
export interface AppError extends Error {
  code?: string;
  details?: any;
  userMessage?: string;
}

// Component prop types
export interface ChatInputProps {
  onSendMessage: (content: string, fileIds: number[]) => Promise<void>;
  disabled?: boolean;
  chatId?: number;
}

export interface ChatMessageProps {
  message: APIMessage;
}

export interface ChatSidebarProps {
  chats: APIChat[];
  selectedChat: APIChat | null;
  onSelectChat: (chat: APIChat) => void;
  onCreateChat: () => void;
  onLogout: () => Promise<void>;
}

export interface FileAttachmentPreviewProps {
  files: APIFile[];
  onRemove: (id: number) => void;
  disabled?: boolean;
}

// Context types
export interface AuthContextType {
  user: User | null;
  loading: boolean;
  error?: string;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}

// Type aliases for convenience
export type Chat = APIChat;
export type Message = APIMessage;
export type File = APIFile;

// Billing related types
export interface SubscriptionPlan {
  id: number;
  name: string;
  price_usd: number;
  monthly_pft: number;
  overage_pft_price: number;
  created_at: string;
  period_end?: string;
}

export interface Usage {
  total_pft: number;
  input_pft: number;
  output_pft: number;
  storage_pft: number;
  base_cost_usd: number;
  overage_cost_usd: number;
}

export interface UsageResponse {
  usage: Usage;
  input_tokens: number;
  output_tokens: number;
  storage_bytes: number;
  subscription?: {
    tier_name: string;
    price_usd: number;
    monthly_pft: number;
    current_period_end: string;
  };
  limits: {
    monthly_pft: number;
    remaining_pft: number;
  };
  history: Array<{
    date: string;
    pft_used: number;
  }>;
}

export interface UserBillingData {
  id: string;
  email: string;
  subscription: {
    tier: string;
    price_usd: number;
    monthly_pft: number;
  };
  usage: {
    total_pft: number;
    overage_cost_usd: number;
  };
}