"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { RefreshCw, Filter } from "lucide-react"
import { getLogs, LogEntry } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

type LogLevel = "ALL" | "INFO" | "WARNING" | "ERROR" | "DEBUG"

export function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedLevel, setSelectedLevel] = useState<LogLevel>("ALL")
  const { toast } = useToast();

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getLogs();
      // Reverse logs to show newest first
      setLogs(data.logs.slice().reverse());
    } catch (error) {
      console.error("Failed to fetch logs:", error)
      toast({
        title: "Error Fetching Logs",
        description: "Could not retrieve logs from the backend.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [toast]);

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchLogs()
  }

  const handleLevelFilter = (level: LogLevel) => {
    setSelectedLevel(level)
  }

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
  }

  const getLevelBadge = (level: string) => {
    switch (level) {
      case "INFO":
        return (
          <Badge variant="default" className="bg-blue-100 text-blue-800 hover:bg-blue-100">
            INFO
          </Badge>
        )
      case "WARNING":
        return (
          <Badge variant="default" className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
            WARNING
          </Badge>
        )
      case "ERROR":
        return <Badge variant="destructive">ERROR</Badge>
      case "DEBUG":
        return (
          <Badge variant="secondary" className="bg-gray-100 text-gray-800 hover:bg-gray-100">
            DEBUG
          </Badge>
        )
      default:
        return <Badge variant="secondary">{level}</Badge>
    }
  }

  const getLogCounts = () => {
    const counts = {
      INFO: logs.filter((log) => log.level === "INFO").length,
      WARNING: logs.filter((log) => log.level === "WARNING").length,
      ERROR: logs.filter((log) => log.level === "ERROR").length,
      DEBUG: logs.filter((log) => log.level === "DEBUG").length,
    }
    return counts
  }

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  useEffect(() => {
    if (selectedLevel === "ALL") {
      setFilteredLogs(logs)
    } else {
      setFilteredLogs(logs.filter((log) => log.level === selectedLevel))
    }
  }, [logs, selectedLevel])

  const logCounts = getLogCounts()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Logs</h1>
          <p className="text-muted-foreground mt-2">View application logs and system events</p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing}
          variant="outline"
          className="flex items-center gap-2 bg-transparent"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Log Level Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-blue-600">{logCounts.INFO}</div>
              <Badge variant="default" className="bg-blue-100 text-blue-800">
                INFO
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Information logs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-yellow-600">{logCounts.WARNING}</div>
              <Badge variant="default" className="bg-yellow-100 text-yellow-800">
                WARNING
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Warning logs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-red-600">{logCounts.ERROR}</div>
              <Badge variant="destructive">ERROR</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Error logs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-gray-600">{logCounts.DEBUG}</div>
              <Badge variant="secondary">DEBUG</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Debug logs</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Application Logs</CardTitle>
              <CardDescription>System events and application messages</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={selectedLevel} onValueChange={handleLevelFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Filter by level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Levels</SelectItem>
                  <SelectItem value="INFO">INFO</SelectItem>
                  <SelectItem value="WARNING">WARNING</SelectItem>
                  <SelectItem value="ERROR">ERROR</SelectItem>
                  <SelectItem value="DEBUG">DEBUG</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading logs...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              {selectedLevel === "ALL" ? "No logs found" : `No ${selectedLevel} logs found`}
            </div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-48">Timestamp</TableHead>
                    <TableHead className="w-24">Level</TableHead>
                    <TableHead>Message</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.map((log, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono text-sm">{formatDateTime(log.timestamp)}</TableCell>
                      <TableCell>{getLevelBadge(log.level)}</TableCell>
                      <TableCell className="font-mono text-sm">{log.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {filteredLogs.length > 0 && (
        <div className="text-sm text-muted-foreground text-center">
          Showing {filteredLogs.length} of {logs.length} log entries
          {selectedLevel !== "ALL" && ` (filtered by ${selectedLevel})`}
        </div>
      )}
    </div>
  )
}
