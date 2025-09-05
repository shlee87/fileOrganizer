"use client"

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react"
import type { ServiceStatus, ProcessedFile } from "@/lib/api";

interface WebSocketMessage {
  type: "status_update" | "file.processed" | "ping";
  data: any
}

interface WebSocketContextType {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  sendMessage: (message: any) => void
}

const WebSocketContext = createContext<WebSocketContextType | null>(null)

interface WebSocketProviderProps {
  children: ReactNode
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 10; // Allow more reconnect attempts

  const connect = () => {
    try {
      const ws = new WebSocket("ws://localhost:8080/api/v1/ws")

      ws.onopen = () => {
        console.log("[WS] WebSocket connected")
        setIsConnected(true)
        reconnectAttempts.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          if (message.type === 'ping') return; // Ignore ping messages
          console.log("[WS] WebSocket message received:", message)
          setLastMessage(message)
        } catch (error) {
          console.error("[WS] Failed to parse WebSocket message:", error)
        }
      }

      ws.onclose = () => {
        console.log("[WS] WebSocket disconnected")
        setIsConnected(false)
        wsRef.current = null

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts.current) * 1000
          console.log(`[WS] Attempting to reconnect in ${delay}ms...`)

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++
            connect()
          }, delay)
        }
      }

      ws.onerror = (error) => {
        console.error("[WS] WebSocket error:", error)
      }

      wsRef.current = ws
    } catch (error) {
      console.error("[WS] Failed to create WebSocket connection:", error)
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }

  useEffect(() => {
    connect()

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return (
    <WebSocketContext.Provider value={{ isConnected, lastMessage, sendMessage }}>{children}</WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error("useWebSocket must be used within a WebSocketProvider")
  }
  return context
}

// Specific hooks for different message types
export function useServiceStatusUpdates() {
  const { lastMessage } = useWebSocket()
  const [statusUpdate, setStatusUpdate] = useState<ServiceStatus | null>(null)

  useEffect(() => {
    if (lastMessage?.type === "status_update") {
      setStatusUpdate(lastMessage.data as ServiceStatus)
    }
  }, [lastMessage])

  return statusUpdate
}

export function useFileProcessedUpdates() {
  const { lastMessage } = useWebSocket()
  const [fileUpdate, setFileUpdate] = useState<ProcessedFile | null>(null)

  useEffect(() => {
    if (lastMessage?.type === "file.processed") {
      setFileUpdate(lastMessage.data as ProcessedFile)
    }
  }, [lastMessage])

  return fileUpdate
}
