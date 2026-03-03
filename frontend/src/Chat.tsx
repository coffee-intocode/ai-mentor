import { Conversation, ConversationContent, ConversationScrollButton } from '@/components/ai-elements/conversation'
import { Loader } from '@/components/ai-elements/loader'
import {
  PromptInput,
  PromptInputButton,
  PromptInputModelSelect,
  PromptInputModelSelectContent,
  PromptInputModelSelectItem,
  PromptInputModelSelectTrigger,
  PromptInputModelSelectValue,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from '@/components/ai-elements/prompt-input'
import { Source, Sources, SourcesContent, SourcesTrigger } from '@/components/ai-elements/sources'
import { DropdownMenu, DropdownMenuContent, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Switch } from '@/components/ui/switch'
import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import type { UIMessage } from 'ai'
import { Settings2Icon } from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent } from 'react'

import { API_ENDPOINTS } from '@/config'
import { useAuth } from '@/context/AuthContext'
import { getToolIcon } from '@/lib/tool-icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useConversationIdFromUrl } from './hooks/useConversationIdFromUrl'
import { Part } from './Part'

interface ModelConfig {
  id: string
  name: string
  builtin_tools: string[]
}

interface BuiltinTool {
  name: string
  id: string
}

interface RemoteConfig {
  models: ModelConfig[]
  builtinTools: BuiltinTool[]
}

interface ConversationResponse {
  id: number
  owner_id: number
  title: string | null
  created_at: string
  updated_at: string
}

interface BackendMessage {
  id: number
  conversation_id: number
  owner_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  parts_json: Array<Record<string, unknown>>
  client_message_id: string | null
  superseded_by_message_id: number | null
  created_at: string
}

async function getModels(token: string) {
  const res = await fetch(API_ENDPOINTS.configure, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error('Failed to fetch config')
  }
  return (await res.json()) as RemoteConfig
}

async function createConversation(token: string, title: string | null = null): Promise<ConversationResponse> {
  const res = await fetch(API_ENDPOINTS.conversations, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(title ? { title } : {}),
  })
  if (!res.ok) {
    throw new Error('Failed to create conversation')
  }
  return (await res.json()) as ConversationResponse
}

async function getConversationMessages(token: string, conversationId: number): Promise<BackendMessage[]> {
  const res = await fetch(API_ENDPOINTS.conversationMessages(conversationId), {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    throw new Error('Failed to fetch conversation messages')
  }
  return (await res.json()) as BackendMessage[]
}

function conversationPathToId(pathname: string): number | null {
  if (pathname === '/') {
    return null
  }

  const maybeId = pathname.startsWith('/') ? pathname.slice(1) : pathname
  const parsed = Number.parseInt(maybeId, 10)
  return Number.isNaN(parsed) ? null : parsed
}

function toUiMessage(message: BackendMessage): UIMessage {
  const parts =
    Array.isArray(message.parts_json) && message.parts_json.length > 0
      ? (message.parts_json as UIMessage['parts'])
      : ([{ type: 'text', text: message.content }] as UIMessage['parts'])

  return {
    id: message.client_message_id ?? `db-${message.id}`,
    role: message.role,
    parts,
  } as UIMessage
}

const Chat = () => {
  const [input, setInput] = useState('')
  const [model, setModel] = useState<string>('')
  const [enabledTools, setEnabledTools] = useState<string[]>([])
  const { session } = useAuth()
  const [conversationId, setConversationId] = useConversationIdFromUrl()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const pendingInitialHydrationConversationIdRef = useRef<number | null>(null)
  const queryClient = useQueryClient()

  const conversationNumericId = useMemo(() => conversationPathToId(conversationId), [conversationId])

  const chatTransport = useMemo(
    () =>
      new DefaultChatTransport({
        api: API_ENDPOINTS.chatStream,
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : undefined,
      }),
    [session?.access_token],
  )

  const { messages, sendMessage, status, setMessages, regenerate } = useChat({
    transport: chatTransport,
    onFinish: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] }).catch((error: unknown) => {
        console.error('Error refreshing conversations:', error)
      })
    },
  })

  const configQuery = useQuery({
    queryFn: () => getModels(session?.access_token ?? ''),
    queryKey: ['models'],
    enabled: Boolean(session?.access_token),
  })

  useEffect(() => {
    if (configQuery.data && !model) {
      setModel(configQuery.data.models[0].id)
    }
  }, [configQuery.data, model])

  const fetchConversationFromDb = useCallback(
    async (token: string, targetConversationId: number) => {
      const storedMessages = await getConversationMessages(token, targetConversationId)
      return storedMessages.map(toUiMessage)
    },
    [],
  )

  useEffect(() => {
    const token = session?.access_token
    if (!token) {
      return
    }

    if (conversationNumericId === null) {
      setMessages([])
      return
    }

    if (pendingInitialHydrationConversationIdRef.current === conversationNumericId) {
      return
    }

    let isCancelled = false
    fetchConversationFromDb(token, conversationNumericId)
      .then((storedMessages) => {
        if (isCancelled) {
          return
        }
        setMessages(storedMessages)
      })
      .catch((error: unknown) => {
        console.error('Error loading conversation history:', error)
      })

    return () => {
      isCancelled = true
    }
  }, [conversationNumericId, fetchConversationFromDb, session?.access_token, setMessages])

  useLayoutEffect(() => {
    textareaRef.current?.focus()
  }, [conversationId])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmedInput = input.trim()
    if (!trimmedInput || !session?.access_token) {
      return
    }

    const send = async () => {
      let activeConversationId = conversationNumericId
      if (activeConversationId === null) {
        const newConversation = await createConversation(session.access_token, trimmedInput.slice(0, 120))
        activeConversationId = newConversation.id
        pendingInitialHydrationConversationIdRef.current = newConversation.id
        setConversationId(`/${newConversation.id}`)
        await queryClient.invalidateQueries({ queryKey: ['conversations'] })
      }

      setInput('')
      try {
        await sendMessage(
          { text: trimmedInput },
          {
            body: { model, builtinTools: enabledTools, conversationId: activeConversationId, webSearch: true },
          },
        )

        const storedMessages = await fetchConversationFromDb(session.access_token, activeConversationId)
        setMessages(storedMessages)
      } finally {
        if (pendingInitialHydrationConversationIdRef.current === activeConversationId) {
          pendingInitialHydrationConversationIdRef.current = null
        }
      }
    }

    send().catch((error: unknown) => {
      console.error('Error sending message:', error)
    })
  }

  function regen(messageId: string) {
    if (conversationNumericId === null) {
      return
    }

    regenerate({
      messageId,
      body: { model, builtinTools: enabledTools, conversationId: conversationNumericId, webSearch: true },
    }).catch((error: unknown) => {
      console.error('Error regenerating message:', error)
    })
  }

  const availableTools = useMemo(() => {
    const enabledToolIds = configQuery.data?.models.find((entry) => entry.id === model)?.builtin_tools ?? []
    return configQuery.data?.builtinTools.filter((tool) => enabledToolIds.includes(tool.id)) ?? []
  }, [configQuery.data, model])

  return (
    <>
      <Conversation className="h-full">
        <ConversationContent>
          {messages.map((message) => (
            <div key={message.id}>
              {message.role === 'assistant' &&
                message.parts.filter((part) => part.type === 'source-url').length > 0 && (
                  <Sources>
                    <SourcesTrigger count={message.parts.filter((part) => part.type === 'source-url').length} />
                    {message.parts
                      .filter((part) => part.type === 'source-url')
                      .map((part, i) => (
                        <SourcesContent key={`${message.id}-${i}`}>
                          <Source key={`${message.id}-${i}`} href={part.url} title={part.url} />
                        </SourcesContent>
                      ))}
                  </Sources>
                )}
              {message.parts.map((part, i) => (
                <Part
                  key={`${message.id}-${i}`}
                  part={part}
                  message={message}
                  status={status}
                  index={i}
                  regen={regen}
                  lastMessage={message.id === messages.at(-1)?.id}
                />
              ))}
            </div>
          ))}
          {status === 'submitted' && <Loader />}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="sticky bottom-0 p-3">
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputTextarea
            ref={textareaRef}
            onChange={(e) => {
              setInput(e.target.value)
            }}
            value={input}
            autoFocus={true}
          />
          <PromptInputToolbar>
            <PromptInputTools>
              {availableTools.length > 0 && (
                <DropdownMenu>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <DropdownMenuTrigger asChild>
                        <PromptInputButton variant="outline">
                          <Settings2Icon className="size-4" />
                        </PromptInputButton>
                      </DropdownMenuTrigger>
                    </TooltipTrigger>
                    <TooltipContent>Tools</TooltipContent>
                  </Tooltip>
                  <DropdownMenuContent align="start">
                    {availableTools.map((tool) => (
                      <div
                        key={tool.id}
                        className="flex items-center justify-between gap-3 px-2 py-1.5 cursor-pointer hover:bg-accent rounded-sm"
                        onClick={() => {
                          setEnabledTools((prev) =>
                            prev.includes(tool.id) ? prev.filter((id) => id !== tool.id) : [...prev, tool.id],
                          )
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {getToolIcon(tool.id)}
                          <span className="text-sm">{tool.name}</span>
                        </div>
                        <Switch
                          checked={enabledTools.includes(tool.id)}
                          onCheckedChange={(checked) => {
                            setEnabledTools((prev) =>
                              checked ? [...prev, tool.id] : prev.filter((id) => id !== tool.id),
                            )
                          }}
                          onClick={(e) => {
                            e.stopPropagation()
                          }}
                        />
                      </div>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
              {configQuery.data && model && (
                <PromptInputModelSelect
                  onValueChange={(value) => {
                    setModel(value)
                  }}
                  value={model}
                >
                  <PromptInputModelSelectTrigger>
                    <PromptInputModelSelectValue />
                  </PromptInputModelSelectTrigger>
                  <PromptInputModelSelectContent>
                    {(configQuery.data as { models: { id: string; name: string }[] }).models.map((modelOption) => (
                      <PromptInputModelSelectItem key={modelOption.id} value={modelOption.id}>
                        {modelOption.name}
                      </PromptInputModelSelectItem>
                    ))}
                  </PromptInputModelSelectContent>
                </PromptInputModelSelect>
              )}
            </PromptInputTools>
            <PromptInputSubmit disabled={!input.trim()} status={status} />
          </PromptInputToolbar>
        </PromptInput>
      </div>
    </>
  )
}

export default Chat
