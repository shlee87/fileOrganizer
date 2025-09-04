"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { RefreshCw } from "lucide-react"
import { useFileProcessedUpdates } from "@/hooks/use-websocket"
import { getRecentFiles, ProcessedFile } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export function RecentActivityPage() {
  const [files, setFiles] = useState<ProcessedFile[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const { toast } = useToast()

  const fileUpdate = useFileProcessedUpdates()

  const fetchRecentFiles = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getRecentFiles();
      setFiles(data.files);
    } catch (error) {
      console.error("Failed to fetch recent files:", error)
      toast({
        title: "Error Fetching Recent Files",
        description: "Could not retrieve recent files from the backend.",
        variant: "destructive",
      })
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    if (fileUpdate) {
      console.log("[v0] Received file update:", fileUpdate)
      // Add the new file to the top of the list, preventing duplicates
      setFiles((prevFiles) => {
        if (prevFiles.some(f => f.id === fileUpdate.id)) {
          return prevFiles.map(f => f.id === fileUpdate.id ? fileUpdate : f);
        }
        return [fileUpdate, ...prevFiles];
      });
    }
  }, [fileUpdate])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchRecentFiles()
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 B"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i]
  }

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString)
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "processed":
        return (
          <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100">
            Processed
          </Badge>
        )
      case "failed":
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const truncatePath = (path: string, maxLength = 50) => {
    if (!path || path.length <= maxLength) return path
    const start = path.substring(0, 20)
    const end = path.substring(path.length - 25)
    return `${start}...${end}`
  }

  useEffect(() => {
    fetchRecentFiles()
  }, [fetchRecentFiles])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Recent Activity</h1>
          <p className="text-muted-foreground mt-2">View recently processed files and their status</p>
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

      <Card>
        <CardHeader>
          <CardTitle>Recent Files</CardTitle>
          <CardDescription>Files that have been processed by the organizer service</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-muted-foreground">Loading recent files...</div>
          ) : files.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No recent files found</div>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Original Path</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Processed At</TableHead>
                    <TableHead className="text-right">Size</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {files.map((file) => (
                    <TableRow key={file.id}>
                      <TableCell className="font-mono text-sm">
                        <div title={file.original_path}>{truncatePath(file.original_path)}</div>
                        {file.destination_path && (
                          <div className="text-xs text-muted-foreground mt-1" title={file.destination_path}>
                            → {truncatePath(file.destination_path)}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{getStatusBadge(file.status)}</TableCell>
                      <TableCell>{formatDateTime(file.processed_at)}</TableCell>
                      <TableCell className="text-right font-mono">{formatFileSize(file.file_size_bytes)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
