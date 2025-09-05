"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { DashboardPage } from "@/components/pages/dashboard-page"
import { RecentActivityPage } from "@/components/pages/recent-activity-page"
import { FilePreviewPage } from "@/components/pages/file-preview-page"
import { ConfigurationPage } from "@/components/pages/configuration-page"
import { LogsPage } from "@/components/pages/logs-page"
import { WebSocketProvider } from "@/hooks/use-websocket"

export type PageType = "dashboard" | "recent-activity" | "file-preview" | "configuration" | "logs"

export default function HomePage() {
  const [currentPage, setCurrentPage] = useState<PageType>("dashboard")

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <DashboardPage />
      case "recent-activity":
        return <RecentActivityPage />
      case "file-preview":
        return <FilePreviewPage />
      case "configuration":
        return <ConfigurationPage />
      case "logs":
        return <LogsPage />
      default:
        return <DashboardPage />
    }
  }

  return (
    <WebSocketProvider>
      <div className="flex h-screen bg-background">
        <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
        <main className="flex-1 overflow-auto">
          <div className="p-6">{renderPage()}</div>
        </main>
      </div>
    </WebSocketProvider>
  )
}
