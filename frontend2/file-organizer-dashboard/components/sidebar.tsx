"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { LayoutDashboard, Clock, Eye, Settings, FileText, Wifi, WifiOff } from "lucide-react"
import type { PageType } from "@/app/page"
import { useWebSocket } from "@/hooks/use-websocket"

interface SidebarProps {
  currentPage: PageType
  onPageChange: (page: PageType) => void
}

const navigationItems = [
  {
    id: "dashboard" as PageType,
    label: "Dashboard",
    icon: LayoutDashboard,
  },
  {
    id: "recent-activity" as PageType,
    label: "Recent Activity",
    icon: Clock,
  },
  {
    id: "file-preview" as PageType,
    label: "File Preview",
    icon: Eye,
  },
  {
    id: "configuration" as PageType,
    label: "Configuration",
    icon: Settings,
  },
  {
    id: "logs" as PageType,
    label: "Logs",
    icon: FileText,
  },
]

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const { isConnected } = useWebSocket()

  return (
    <div className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col">
      <div className="p-6 border-b border-sidebar-border">
        <h1 className="text-xl font-semibold text-sidebar-foreground">File Organizer</h1>
        <div className="flex items-center justify-between mt-1">
          <p className="text-sm text-muted-foreground">Service Dashboard</p>
          <div className="flex items-center gap-1">
            {isConnected ? <Wifi className="h-3 w-3 text-green-500" /> : <WifiOff className="h-3 w-3 text-red-500" />}
            <span className="text-xs text-muted-foreground">{isConnected ? "Live" : "Offline"}</span>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon
          const isActive = currentPage === item.id

          return (
            <Button
              key={item.id}
              variant={isActive ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-start gap-3 h-11",
                isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
              )}
              onClick={() => onPageChange(item.id)}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Button>
          )
        })}
      </nav>
    </div>
  )
}
