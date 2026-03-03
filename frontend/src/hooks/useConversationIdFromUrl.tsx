import { useLocation, useNavigate } from 'react-router-dom'

export function useConversationIdFromUrl(): [string, (id: string) => void] {
  const location = useLocation()
  const navigate = useNavigate()

  const setConversationIdAndUrl = (id: string) => {
    navigate(id || '/')
  }

  return [location.pathname, setConversationIdAndUrl]
}
