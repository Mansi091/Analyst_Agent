"use client"

import { useCallback, useRef, useState } from "react"
import { Upload, FileSpreadsheet, X, Table2 } from "lucide-react"
import { buildSchema, isNumericDtype } from "@/lib/csv"
import { SAMPLE_CSV, SAMPLE_CSV_NAME } from "@/lib/sample-data"
import type { DatasetSchema } from "@/lib/types"
import { Button } from "@/components/ui/button"

type Props = {
  schema: DatasetSchema | null
  onSchema: (schema: DatasetSchema | null) => void
  onFile?: (file: File | null) => void
  disabled?: boolean
}

export function CsvUploader({ schema, onSchema, onFile, disabled }: Props) {
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback(
    async (file: File) => {
      setError(null)
      if (!file.name.toLowerCase().endsWith(".csv")) {
        setError("Please upload a .csv file.")
        return
      }
      try {
        const text = await file.text()
        const parsed = buildSchema(file.name, text)
        if (parsed.columns.length === 0) {
          setError("Could not detect any columns in that file.")
          return
        }
        onSchema(parsed)
        onFile?.(file)
      } catch {
        setError("Failed to read that file.")
      }
    },
    [onSchema],
  )

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      if (disabled) return
      const file = e.dataTransfer.files?.[0]
      if (file) handleFile(file)
    },
    [disabled, handleFile],
  )

  if (schema) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <FileSpreadsheet className="size-4 shrink-0 text-primary" aria-hidden />
            <span className="truncate font-mono text-sm text-card-foreground">{schema.fileName}</span>
          </div>
          <button
            type="button"
            onClick={() => { onSchema(null); onFile?.(null) }}
            disabled={disabled}
            className="flex size-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-40"
            aria-label="Remove dataset"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 px-4 py-2.5 text-xs text-muted-foreground">
          <Table2 className="size-3.5" aria-hidden />
          <span className="font-mono">
            {schema.rowCount.toLocaleString()} rows · {schema.columns.length} columns
          </span>
        </div>

        <ul className="max-h-64 overflow-auto border-t border-border px-2 py-2">
          {schema.columns.map((col) => (
            <li
              key={col.name}
              className="flex items-center justify-between gap-3 rounded-md px-2 py-1.5 hover:bg-muted/50"
            >
              <span className="truncate font-mono text-sm text-card-foreground">{col.name}</span>
              <span
                className={`shrink-0 rounded px-1.5 py-0.5 font-mono text-[11px] ${
                  isNumericDtype(col.dtype)
                    ? "bg-primary/15 text-primary"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {col.dtype}
              </span>
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) inputRef.current?.click()
        }}
        className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed px-6 py-10 text-center transition-colors ${
          dragging ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/50"
        } ${disabled ? "pointer-events-none opacity-50" : ""}`}
      >
        <div className="flex size-11 items-center justify-center rounded-full bg-primary/10">
          <Upload className="size-5 text-primary" aria-hidden />
        </div>
        <div>
          <p className="text-sm font-medium text-card-foreground">Drop a CSV file here</p>
          <p className="mt-1 text-xs text-muted-foreground">or click to browse your files</p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) handleFile(file)
            e.target.value = ""
          }}
        />
      </div>

      {error && <p className="mt-2 text-xs text-destructive">{error}</p>}

      <Button
        variant="ghost"
        size="sm"
        disabled={disabled}
        onClick={() => onSchema(buildSchema(SAMPLE_CSV_NAME, SAMPLE_CSV))}
        className="mt-2 w-full text-xs text-muted-foreground hover:text-foreground"
      >
        Or load a sample dataset
      </Button>
    </div>
  )
}
