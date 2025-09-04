"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { RefreshCw, File, CheckCircle, XCircle, ArrowRight } from "lucide-react"
import { getFilePreview, PreviewFile, FilePreviewResponse } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

export function FilePreviewPage() {
  const [previewData, setPreviewData] = useState<FilePreviewResponse | null>(null);
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const { toast } = useToast();

  const fetchFilePreview = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFilePreview();
      setPreviewData(data);
    } catch (error) {
      console.error("Failed to fetch file preview:", error)
      toast({
        title: "Error Fetching File Preview",
        description: "Could not retrieve file preview from the backend.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [toast]);

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchFilePreview()
  }

  const getProcessBadge = (wouldProcess: boolean) => {
    if (wouldProcess) {
      return (
        <Badge variant="default" className="bg-green-100 text-green-800 hover:bg-green-100 flex items-center gap-1">
          <CheckCircle className="h-3 w-3" />
          Will Process
        </Badge>
      )
    } else {
      return (
        <Badge variant="secondary" className="bg-red-100 text-red-800 hover:bg-red-100 flex items-center gap-1">
          <XCircle className="h-3 w-3" />
          Will Skip
        </Badge>
      )
    }
  }

  const getFileIcon = (filePath: string) => {
    return <File className="h-4 w-4 text-muted-foreground" />
  }

  useEffect(() => {
    fetchFilePreview()
  }, [fetchFilePreview])

  const files = previewData?.files ?? [];
  const summary = previewData?.summary;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">File Preview</h1>
          <p className="text-muted-foreground mt-2">Preview files in the workplace and see what would be processed</p>
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

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading file preview...</div>
      ) : files.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <File className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">No Files Found</h3>
            <p className="text-muted-foreground">No files are currently in the workplace directory</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {files.map((file, index) => (
            <Card key={index} className="transition-shadow hover:shadow-md">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {getFileIcon(file.file_path)}
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-base font-mono truncate" title={file.file_path}>
                        {file.file_path}
                      </CardTitle>
                    </div>
                  </div>
                  {getProcessBadge(file.would_process)}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Reason:</p>
                    <p className="text-sm">{file.reason}</p>
                  </div>

                  {file.would_process && file.destination_path && (
                    <div className="bg-muted/50 rounded-lg p-3">
                      <p className="text-sm text-muted-foreground mb-2">Destination Path:</p>
                      <div className="flex items-center gap-2 text-sm font-mono">
                        <span className="text-muted-foreground truncate">{file.file_path}</span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                        <span className="text-foreground truncate" title={file.destination_path}>
                          {file.destination_path}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {summary && files.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>Total files: {summary.total_files}</span>
              <div className="flex gap-4">
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3 text-green-600" />
                  Will process: {summary.would_process}
                </span>
                <span className="flex items-center gap-1">
                  <XCircle className="h-3 w-3 text-red-600" />
                  Will skip: {summary.would_skip}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
