"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import { Save, RefreshCw, Settings } from "lucide-react"
import { getConfiguration, saveConfiguration, Configuration } from "@/lib/api"

const initialConfig: Configuration = {
  workplace_path: "",
  destination_root: "",
  stability_wait_seconds: 10,
  dry_run_mode: false,
  status_keywords: ["signed", "executed", "final"],
  filename_pattern: "",
  log_level: "INFO",
};

export function ConfigurationPage() {
  const [config, setConfig] = useState<Configuration>(initialConfig)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const { toast } = useToast()

  const fetchConfiguration = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getConfiguration();
      setConfig(data);
    } catch (error) {
      console.error("Failed to fetch configuration:", error)
      toast({
        title: "Error Fetching Configuration",
        description: "Could not retrieve settings from the backend.",
        variant: "destructive",
      })
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [toast])

  const handleSaveConfiguration = async () => {
    setSaving(true)
    try {
      await saveConfiguration(config);
      toast({
        title: "Configuration Saved",
        description: "Your settings have been updated successfully.",
      })
    } catch (error) {
      console.error("Failed to save configuration:", error)
      toast({
        title: "Error Saving Configuration",
        description: String(error),
        variant: "destructive",
      })
    } finally {
      setSaving(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchConfiguration()
  }

  const handleInputChange = (field: keyof Configuration, value: string | number | boolean) => {
    setConfig((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  useEffect(() => {
    fetchConfiguration()
  }, [fetchConfiguration])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Configuration</h1>
          <p className="text-muted-foreground mt-2">Manage service settings and preferences</p>
        </div>
        <div className="text-center py-12 text-muted-foreground">Loading configuration...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Configuration</h1>
          <p className="text-muted-foreground mt-2">Manage service settings and preferences</p>
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

      <div className="grid gap-6 max-w-2xl">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Service Configuration
            </CardTitle>
            <CardDescription>Configure the file organizer service settings and behavior</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="workplace-path">Workplace Path</Label>
              <Input
                id="workplace-path"
                type="text"
                value={config.workplace_path}
                onChange={(e) => handleInputChange("workplace_path", e.target.value)}
                placeholder="/path/to/workplace"
                className="font-mono"
              />
              <p className="text-sm text-muted-foreground">The directory where files are monitored for processing</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="destination-root">Destination Root</Label>
              <Input
                id="destination-root"
                type="text"
                value={config.destination_root}
                onChange={(e) => handleInputChange("destination_root", e.target.value)}
                placeholder="/path/to/destination"
                className="font-mono"
              />
              <p className="text-sm text-muted-foreground">The root directory where organized files will be moved</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="stability-wait">Stability Wait Seconds</Label>
              <Input
                id="stability-wait"
                type="number"
                min="1"
                max="300"
                value={config.stability_wait_seconds}
                onChange={(e) => handleInputChange("stability_wait_seconds", Number.parseInt(e.target.value) || 10)}
                placeholder="10"
              />
              <p className="text-sm text-muted-foreground">
                Time to wait (in seconds) before processing a file to ensure it's stable
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="dry-run"
                checked={config.dry_run_mode}
                onCheckedChange={(checked) => handleInputChange("dry_run_mode", checked as boolean)}
              />
              <div className="grid gap-1.5 leading-none">
                <Label
                  htmlFor="dry-run"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  Dry Run Mode
                </Label>
                <p className="text-xs text-muted-foreground">
                  When enabled, files will be analyzed but not actually moved
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Current Settings Summary</CardTitle>
            <CardDescription>Review your current configuration</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Workplace:</span>
                <span className="font-mono">{config.workplace_path || "Not set"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Destination:</span>
                <span className="font-mono">{config.destination_root || "Not set"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Stability Wait:</span>
                <span>{config.stability_wait_seconds} seconds</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mode:</span>
                <span className={config.dry_run_mode ? "text-yellow-600" : "text-green-600"}>
                  {config.dry_run_mode ? "Dry Run" : "Live Processing"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button onClick={handleSaveConfiguration} disabled={saving} className="flex items-center gap-2">
            <Save className="h-4 w-4" />
            {saving ? "Saving..." : "Save Configuration"}
          </Button>
        </div>
      </div>
    </div>
  )
}
