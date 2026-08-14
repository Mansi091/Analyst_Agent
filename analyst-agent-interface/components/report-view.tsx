"use client"

import { FileText } from "lucide-react"
import type { ReactNode } from "react"

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g
  const parts = text.split(regex)
  parts.forEach((part, i) => {
    if (!part) return
    if (part.startsWith("**") && part.endsWith("**")) {
      nodes.push(
        <strong key={`${keyPrefix}-${i}`} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>,
      )
    } else if (part.startsWith("`") && part.endsWith("`")) {
      nodes.push(
        <code key={`${keyPrefix}-${i}`} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em] text-primary">
          {part.slice(1, -1)}
        </code>,
      )
    } else {
      nodes.push(part)
    }
  })
  return nodes
}

function MarkdownReport({ markdown }: { markdown: string }) {
  const lines = markdown.split("\n")
  const blocks: ReactNode[] = []
  let listBuffer: { type: "ol" | "ul"; text: string }[] = []

  const flushList = () => {
    if (listBuffer.length === 0) return
    const isOrdered = listBuffer[0].type === "ol"
    blocks.push(
      <div key={`list-${blocks.length}`} className="my-2 flex flex-col gap-2">
        {listBuffer.map((item, i) => (
          <div key={i} className="flex gap-2.5 text-sm leading-relaxed text-muted-foreground">
            {item.type === "ol" ? (
              <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-primary/15 font-mono text-[11px] text-primary">
                {i + 1}
              </span>
            ) : (
              <span className="mt-2.5 size-1.5 shrink-0 rounded-full bg-primary/50" />
            )}
            <span className="text-pretty">{renderInline(item.text, `li-${i}`)}</span>
          </div>
        ))}
      </div>,
    )
    listBuffer = []
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    if (line.trim() === "") {
      flushList()
      continue
    }
    
    if (/^\d+\.\s/.test(line)) {
      listBuffer.push({ type: "ol", text: line.replace(/^\d+\.\s/, "") })
      continue
    }
    
    if (/^[-*]\s/.test(line)) {
      listBuffer.push({ type: "ul", text: line.replace(/^[-*]\s/, "") })
      continue
    }
    
    flushList()
    if (line.startsWith("### ")) {
      blocks.push(
        <h3 key={blocks.length} className="mt-5 mb-1 text-sm font-semibold uppercase tracking-wide text-primary">
          {line.slice(4)}
        </h3>,
      )
    } else if (line.startsWith("## ")) {
      blocks.push(
        <h2 key={blocks.length} className="mb-1 text-lg font-semibold text-foreground">
          {line.slice(3)}
        </h2>,
      )
    } else if (line.startsWith("> ")) {
      blocks.push(
        <blockquote
          key={blocks.length}
          className="my-3 rounded-r border-l-2 border-primary/50 bg-muted/40 py-2 pl-3 text-xs italic text-muted-foreground"
        >
          {renderInline(line.slice(2), `bq-${blocks.length}`)}
        </blockquote>,
      )
    } else {
      blocks.push(
        <p key={blocks.length} className="text-sm leading-relaxed text-muted-foreground text-pretty">
          {renderInline(line, `p-${blocks.length}`)}
        </p>,
      )
    }
  }
  flushList()

  return <div className="flex flex-col gap-1">{blocks}</div>
}

export function ReportView({ report }: { report: string }) {
  return (
    <div className="rounded-xl border border-primary/25 bg-card">
      <div className="flex items-center gap-2 border-b border-border px-4 py-3">
        <FileText className="size-4 text-primary" aria-hidden />
        <span className="text-sm font-medium text-card-foreground">Final report</span>
      </div>
      <div className="px-4 py-4">
        <MarkdownReport markdown={report} />
      </div>
    </div>
  )
}
