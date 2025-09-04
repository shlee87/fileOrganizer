"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Play, Square, Clock, FileText, Quote as Queue } from "lucide-react"
import { cn } from "@/lib/utils"
import { useServiceStatusUpdates } from "@/hooks/use-websocket"
import { getServiceStatus, startService, stopService, ServiceStatus } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export function DashboardPage() {
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<"start" | "stop" | null>(null)
  const { toast } = useToast()

  const statusUpdate = useServiceStatusUpdates()

  const fetchServiceStatus = useCallback(async () => {
    try {
      const data = await getServiceStatus();
      setServiceStatus(data);
    } catch (error) {
      console.error("Failed to fetch service status:", error)
      setServiceStatus({ status: "error", uptime_seconds: 0, files_processed_today: 0, queue_size: 0, last_error: "Failed to connect to backend" })
      toast({
        title: "Error Fetching Status",
        description: "Could not connect to the backend service.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }, [toast])

  const handleServiceAction = async (action: "start" | "stop") => {
    setActionLoading(action)
    try {
      const actionFunc = action === "start" ? startService : stopService;
      await actionFunc();
      await fetchServiceStatus(); // Refresh status after action
      toast({
        title: `Service ${action}ed`,
        description: `The service has been ${action}ed successfully.`,
      })
    } catch (error) {
      console.error(`Failed to ${action} service:`, error)
      toast({
        title: `Failed to ${action} Service`,
        description: String(error),
        variant: "destructive",
      })
    } finally {
      setActionLoading(null)
    }
  }

  const formatUptime = (seconds: number) => {
    if (seconds < 0) return "0s";
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`
    } else {
      return `${secs}s`
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500"
      case "stopped":
        return "bg-red-500"
      case "error":
        return "bg-yellow-500"
      default:
        return "bg-gray-500"
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "running":
        return "Service is running"
      case "stopped":
        return "Service is stopped"
      case "error":
        return "Service has an error"
      default:
        return "Unknown status"
    }
  }

  useEffect(() => {
    if (statusUpdate) {
      console.log("[v0] Received status update:", statusUpdate)
      setServiceStatus(statusUpdate)
    }
  }, [statusUpdate])

  useEffect(() => {
    fetchServiceStatus()
    // Poll for status updates every 30 seconds as a fallback
    const interval = setInterval(fetchServiceStatus, 30000)
    return () => clearInterval(interval)
  }, [fetchServiceStatus])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-2">Monitor your file organizer service status and metrics</p>
        </div>
        <div className="text-center py-12 text-muted-foreground">Loading service status...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Monitor your file organizer service status and metrics</p>
      </div>

      {/* Service Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            Service Status
            {serviceStatus && (
              <div className="flex items-center gap-2">
                <div className={cn("w-3 h-3 rounded-full", getStatusColor(serviceStatus.status))} />
                <Badge variant={serviceStatus.status === "running" ? "default" : "destructive"}>
                  {serviceStatus.status.toUpperCase()}
                </Badge>
              </div>
            )}
          </CardTitle>
          <CardDescription>Current status of the file organizer service</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {serviceStatus && (
            <>
              <div className="flex items-center gap-4">
                <div className={cn("w-4 h-4 rounded-full", getStatusColor(serviceStatus.status))} />
                <span className="text-lg font-medium">{getStatusText(serviceStatus.status)}</span>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => handleServiceAction("start")}
                  disabled={serviceStatus.status === "running" || actionLoading === "start"}
                  className="flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  {actionLoading === "start" ? "Starting..." : "Start"}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => handleServiceAction("stop")}
                  disabled={serviceStatus.status === "stopped" || actionLoading === "stop"}
                  className="flex items-center gap-2"
                >
                  <Square className="h-4 w-4" />
                  {actionLoading === "stop" ? "Stopping..." : "Stop"}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {serviceStatus ? formatUptime(serviceStatus.uptime_seconds) : "0s"}
            </div>
            <p className="text-xs text-muted-foreground">Service running time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Files Processed Today</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceStatus?.files_processed_today ?? 0}</div>
            <p className="text-xs text-muted-foreground">Files organized today</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Queue Size</CardTitle>
            <Queue className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceStatus?.queue_size ?? 0}</div>
            <p className="text-xs text-muted-foreground">Files waiting to process</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
