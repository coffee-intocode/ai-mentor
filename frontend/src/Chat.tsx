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
import { AlertTriangleIcon, Settings2Icon } from 'lucide-react'
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

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

type UiPart = UIMessage['parts'][number]

type ApiError = Error & {
  status?: number
  statusCode?: number
}

function getErrorStatusCode(error: unknown): number | null {
  if (!error || typeof error !== 'object') {
    return null
  }
  const maybeError = error as ApiError
  if (typeof maybeError.status === 'number') {
    return maybeError.status
  }
  if (typeof maybeError.statusCode === 'number') {
    return maybeError.statusCode
  }
  return null
}

function conversationNotFoundMessage(conversationId: number | null): string {
  return conversationId === null
    ? 'Unable to load conversation'
    : `Unable to load conversation ${conversationId}`
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
    const error = new Error('Failed to fetch conversation messages') as ApiError
    error.status = res.status
    throw error
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function normalizeStoredPart(part: unknown): UiPart | null {
  if (!isRecord(part)) {
    return null
  }

  const type = part.type
  if (typeof type !== 'string') {
    return null
  }

  if (type === 'text' && typeof part.text === 'string') {
    return { type: 'text', text: part.text } as UiPart
  }

  if (type === 'reasoning' && typeof part.text === 'string') {
    return { type: 'reasoning', text: part.text } as UiPart
  }

  if (type === 'source-url' && typeof part.url === 'string') {
    return { type: 'source-url', url: part.url } as UiPart
  }

  if (type === 'file' && typeof part.url === 'string') {
    const normalizedFilePart: { type: 'file'; url: string; mediaType?: string } = {
      type: 'file',
      url: part.url,
    }
    if (typeof part.mediaType === 'string') {
      normalizedFilePart.mediaType = part.mediaType
    }
    return normalizedFilePart as UiPart
  }

  if (typeof part.toolCallId === 'string') {
    const normalizedToolPart: Record<string, unknown> = {
      ...part,
      type,
      toolCallId: part.toolCallId,
    }
    if (typeof normalizedToolPart.state !== 'string') {
      normalizedToolPart.state = 'input-available'
    }
    return normalizedToolPart as UiPart
  }

  return null
}

function normalizeStoredParts(message: BackendMessage): UIMessage['parts'] {
  if (!Array.isArray(message.parts_json) || message.parts_json.length === 0) {
    return [{ type: 'text', text: message.content }] as UIMessage['parts']
  }

  const normalizedParts = message.parts_json
    .map((part) => normalizeStoredPart(part))
    .filter((part): part is UiPart => part !== null)

  if (normalizedParts.length !== message.parts_json.length) {
    console.warn(
      `Dropped unsupported persisted parts while hydrating message ${message.id}: ` +
        `${message.parts_json.length - normalizedParts.length} part(s)`,
    )
  }

  if (normalizedParts.length === 0) {
    return [{ type: 'text', text: message.content }] as UIMessage['parts']
  }

  return normalizedParts as UIMessage['parts']
}

function isSourceUrlPart(part: UiPart): part is UiPart & { type: 'source-url'; url: string } {
  return part.type === 'source-url' && 'url' in part && typeof (part as { url?: unknown }).url === 'string'
}

function toUiMessage(message: BackendMessage): UIMessage {
  return {
    id: message.client_message_id ?? `db-${message.id}`,
    role: message.role,
    parts: normalizeStoredParts(message),
  } as UIMessage
}

const Chat = () => {
  const [input, setInput] = useState('')
  const [model, setModel] = useState<string>('')
  const [enabledTools, setEnabledTools] = useState<string[]>([])
  const [errorBanner, setErrorBanner] = useState<string | null>(null)
  const { session } = useAuth()
  const [conversationId, setConversationId] = useConversationIdFromUrl()
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const pendingInitialHydrationConversationIdRef = useRef<number | null>(null)
  const submitInFlightRef = useRef(false)
  const location = useLocation()
  const navigate = useNavigate()
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

  const redirectToRootWithError = useCallback(
    (message: string) => {
      setMessages([])
      navigate(
        {
          pathname: '/',
          search: `?${new URLSearchParams({ chatError: message }).toString()}`,
        },
        { replace: true },
      )
    },
    [navigate, setMessages],
  )

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const errorMessage = params.get('chatError')
    if (!errorMessage) {
      return
    }

    setErrorBanner(errorMessage)
    params.delete('chatError')
    const nextSearch = params.toString()
    navigate(
      {
        pathname: location.pathname,
        search: nextSearch ? `?${nextSearch}` : '',
      },
      { replace: true },
    )
  }, [location.pathname, location.search, navigate])

  useEffect(() => {
    if (!errorBanner) {
      return
    }

    const timeoutId = window.setTimeout(() => {
      setErrorBanner(null)
    }, 6000)

    return () => {
      window.clearTimeout(timeoutId)
    }
  }, [errorBanner])

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
        if (isCancelled) {
          return
        }
        if (getErrorStatusCode(error) === 404) {
          redirectToRootWithError(conversationNotFoundMessage(conversationNumericId))
          return
        }
        console.error('Error loading conversation history:', error)
      })

    return () => {
      isCancelled = true
    }
  }, [conversationNumericId, fetchConversationFromDb, redirectToRootWithError, session?.access_token, setMessages])

  useLayoutEffect(() => {
    textareaRef.current?.focus()
  }, [conversationId])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (submitInFlightRef.current || status === 'submitted' || status === 'streaming') {
      return
    }

    const trimmedInput = input.trim()
    if (!trimmedInput || !session?.access_token) {
      return
    }

    submitInFlightRef.current = true

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
      } catch (error) {
        const errorCode = getErrorStatusCode(error)
        if (errorCode === 404) {
          redirectToRootWithError(conversationNotFoundMessage(activeConversationId))
          return
        }
        if (errorCode === 409) {
          // Duplicate-submit guard from backend; ignore noisy re-clicks.
          return
        }
        throw error
      } finally {
        if (pendingInitialHydrationConversationIdRef.current === activeConversationId) {
          pendingInitialHydrationConversationIdRef.current = null
        }
      }
    }

    send().catch((error: unknown) => {
      console.error('Error sending message:', error)
    }).finally(() => {
      submitInFlightRef.current = false
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
      if (getErrorStatusCode(error) === 404) {
        redirectToRootWithError(conversationNotFoundMessage(conversationNumericId))
        return
      }
      console.error('Error regenerating message:', error)
    })
  }

  const availableTools = useMemo(() => {
    const enabledToolIds = configQuery.data?.models.find((entry) => entry.id === model)?.builtin_tools ?? []
    return configQuery.data?.builtinTools.filter((tool) => enabledToolIds.includes(tool.id)) ?? []
  }, [configQuery.data, model])

  return (
    <>
      {errorBanner && (
        <div className="fixed left-1/2 top-4 z-50 -translate-x-1/2 px-3">
          <div
            role="alert"
            className="flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-lg"
          >
            <AlertTriangleIcon className="size-4 shrink-0" />
            <span>{errorBanner}</span>
          </div>
        </div>
      )}

      <Conversation className="h-full">
        <ConversationContent>
          {messages.map((message) => (
            <div key={message.id}>
              {message.role === 'assistant' && message.parts.filter(isSourceUrlPart).length > 0 && (
                  <Sources>
                    <SourcesTrigger count={message.parts.filter(isSourceUrlPart).length} />
                    {message.parts
                      .filter(isSourceUrlPart)
                      .map((part, i) => (
                        <SourcesContent key={`${message.id}-${i}`}>
                          <Source href={part.url} title={part.url} />
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
            <PromptInputSubmit
              disabled={!input.trim() || status === 'submitted' || status === 'streaming'}
              status={status}
            />
          </PromptInputToolbar>
        </PromptInput>
      </div>
    </>
  )
}

export default Chat
