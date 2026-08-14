"use client"

import { useState } from "react"
import { Check, ChevronRight, Loader2, TriangleAlert, ListChecks, Terminal } from "lucide-react"
import type { AgentStep } from "@/lib/types"

function StatusIcon({ status }: { status: AgentStep["status"] }) {
  if (status === "running") return <Loader2 className="size-4 animate-spin text-primary" aria-hidden />
  if (status === "error") return <TriangleAlert className="size-4 text-destructive" aria-hidden />
  return <Check className="size-4 text-primary" aria-hidden />
}

export function StepCard({ step }: { step: AgentStep }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="overflow-hidden rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-3 py-2.5 text-left"
      >
        <StatusIcon status={step.status} />
        <span className="flex-1 text-sm text-card-foreground">{step.title}</span>
        <ChevronRight className={`size-4 text-muted-foreground transition-transform ${open ? "rotate-90" : ""}`} />
      </button>

      {open && (
        <div className="border-t border-border">
          {step.code && (
            <div className="border-b border-border bg-background/60">
              <div className="flex items-center gap-1.5 px-3 pt-2 text-[11px] uppercase tracking-wide text-muted-foreground">
                <Terminal className="size-3" aria-hidden /> code
              </div>
              <pre className="overflow-auto px-3 py-2 font-mono text-xs leading-relaxed text-foreground/90">
                {step.code}
              </pre>
            </div>
          )}
          <div>
            <div className="px-3 pt-2 text-[11px] uppercase tracking-wide text-muted-foreground">output</div>
            <pre className="overflow-auto px-3 py-2 font-mono text-xs leading-relaxed text-muted-foreground">
              {step.result}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

export function PlanCard({ plan }: { plan: string[] }) {
  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
        <ListChecks className="size-4 text-primary" aria-hidden />
        <span className="text-sm font-medium text-card-foreground">Analysis plan</span>
        <span className="ml-auto font-mono text-xs text-muted-foreground">{plan.length} steps</span>
      </div>
      <ol className="px-3 py-2">
        {plan.map((item, i) => (
          <li key={i} className="flex gap-3 py-1.5 text-sm text-muted-foreground">
            <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-muted font-mono text-[11px] text-foreground">
              {i + 1}
            </span>
            <span className="leading-relaxed text-pretty">{item}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}

export function PhaseBadge({ phase, message }: { phase: string; message: string }) {
  return (
    <div className="flex items-center gap-2.5 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2.5">
      <Loader2 className="size-4 animate-spin text-primary" aria-hidden />
      <span className="font-mono text-xs uppercase tracking-wide text-primary">{phase}</span>
      <span className="text-sm text-muted-foreground">{message}</span>
    </div>
  )
}
