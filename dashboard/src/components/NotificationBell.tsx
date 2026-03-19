import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { notifications, createNotificationSocket } from '../api/client'
import type { NotificationItem } from '../api/client'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()

  const { data: unreadData } = useQuery({
    queryKey: ['notifications-unread-count'],
    queryFn: () => notifications.unreadCount(),
    refetchInterval: 30000,
  })

  const { data: items } = useQuery({
    queryKey: ['notifications-list'],
    queryFn: () => notifications.list(false, 20),
    enabled: open,
  })

  const unreadCount = unreadData?.count ?? 0

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = createNotificationSocket()
    if (!ws) return

    ws.onmessage = () => {
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
      if (open) {
        queryClient.invalidateQueries({ queryKey: ['notifications-list'] })
      }
    }

    ws.onclose = () => {
      // Reconnect after 5 seconds
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
      }, 5000)
    }

    return () => {
      ws.close()
    }
  }, [queryClient, open])

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleMarkRead = useCallback(
    async (id: string) => {
      await notifications.markRead(id)
      queryClient.invalidateQueries({ queryKey: ['notifications-list'] })
      queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
    },
    [queryClient]
  )

  const handleMarkAllRead = useCallback(async () => {
    await notifications.markAllRead()
    queryClient.invalidateQueries({ queryKey: ['notifications-list'] })
    queryClient.invalidateQueries({ queryKey: ['notifications-unread-count'] })
  }, [queryClient])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-1.5 text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="Notifications"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-white border rounded-lg shadow-lg z-50">
          <div className="flex items-center justify-between px-3 py-2 border-b">
            <span className="text-sm font-medium">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!items || items.length === 0 ? (
              <p className="p-4 text-sm text-gray-500 text-center">
                No notifications
              </p>
            ) : (
              items.map((n: NotificationItem) => (
                <div
                  key={n.id}
                  onClick={() => !n.read && handleMarkRead(n.id)}
                  className={`px-3 py-2 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 ${
                    !n.read ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <p className="text-sm font-medium">{n.title}</p>
                    <span className="text-[10px] text-gray-400 whitespace-nowrap ml-2">
                      {new Date(n.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-0.5">{n.message}</p>
                  <span className="inline-block mt-1 text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                    {n.type}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
