import { CirclePlus, Ellipsis, LogOut, MessageCircle, Trash2, User } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { useAuth } from '@/context/AuthContext'
import { useConversationIdFromUrl } from '@/hooks/useConversationIdFromUrl'
import { cn } from '@/lib/utils'
import { API_ENDPOINTS } from '@/config'
import { ModeToggle } from './mode-toggle'

interface ConversationListItem {
  id: number
  title: string | null
  created_at: string
  updated_at: string
}

async function getConversations(token: string): Promise<ConversationListItem[]> {
  const res = await fetch(API_ENDPOINTS.conversations, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error('Failed to fetch conversations')
  }
  return (await res.json()) as ConversationListItem[]
}

async function deleteConversation(token: string, conversationId: number): Promise<void> {
  const res = await fetch(`${API_ENDPOINTS.conversations}/${conversationId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error('Failed to delete conversation')
  }
}

export function AppSidebar() {
  const [conversationId, setConversationId] = useConversationIdFromUrl()
  const { signOut, session } = useAuth()
  const queryClient = useQueryClient()
  const conversationsQuery = useQuery({
    queryKey: ['conversations'],
    queryFn: () => getConversations(session?.access_token ?? ''),
    enabled: Boolean(session?.access_token),
  })
  const conversations = conversationsQuery.data ?? []

  const handleDeleteConversation = async (targetConversationId: number) => {
    const token = session?.access_token
    if (!token) {
      return
    }

    await deleteConversation(token, targetConversationId)
    await queryClient.invalidateQueries({ queryKey: ['conversations'] })

    if (conversationId === `/${targetConversationId}`) {
      setConversationId('/')
    }
  }

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="mt-4 ml-4 flex items-center">
          <h1 className="text-l font-medium text-balance group-data-[state=collapsed]:invisible truncate whitespace-nowrap">
            Ai Mentor
          </h1>

          <SidebarTrigger className="ml-auto mr-2 group-data-[state=collapsed]:-translate-x-3" />
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarMenu className="mb-2">
            <SidebarMenuItem>
              <SidebarMenuButton asChild tooltip="Start a new conversation">
                <Link to="/">
                  <CirclePlus />
                  <span>New conversation</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>

          <SidebarGroupContent>
            <SidebarMenu>
              {conversations.map((conversation) => (
                <SidebarMenuItem key={conversation.id}>
                  <SidebarMenuButton asChild tooltip={conversation.title ?? `Conversation ${conversation.id}`}>
                    <Link
                      to={`/${conversation.id}`}
                      className={cn('h-auto flex items-start gap-2', {
                        'bg-accent pointer-events-none': `/${conversation.id}` === conversationId,
                      })}
                    >
                      <MessageCircle className="size-3 mt-1" />
                      <span className="flex flex-col items-start">
                        <span className="truncate max-w-[150px]">
                          {conversation.title ?? `Conversation ${conversation.id}`}
                        </span>
                        <span className="text-xs opacity-30">
                          {new Date(conversation.updated_at).toLocaleString()}
                        </span>
                      </span>
                    </Link>
                  </SidebarMenuButton>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuAction
                        showOnHover
                        onClick={(event) => {
                          event.preventDefault()
                          event.stopPropagation()
                        }}
                      >
                        <Ellipsis />
                        <span className="sr-only">Conversation actions</span>
                      </SidebarMenuAction>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent side="right" align="start">
                      <DropdownMenuItem
                        variant="destructive"
                        onClick={(event) => {
                          event.preventDefault()
                          event.stopPropagation()
                          handleDeleteConversation(conversation.id).catch((error: unknown) => {
                            console.error('Error deleting conversation:', error)
                          })
                        }}
                      >
                        <Trash2 />
                        <span>Delete</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <div className="flex items-center justify-between px-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="cursor-pointer rounded-full focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
                <Avatar>
                  <AvatarFallback>
                    <User className="size-4" />
                  </AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent side="top" align="start">
              <DropdownMenuItem
                onClick={() => {
                  signOut().catch(console.error)
                }}
              >
                <LogOut />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <ModeToggle />
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
