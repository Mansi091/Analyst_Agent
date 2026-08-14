"use client"

import { useCallback, useRef, useState } from "react"
import { ArrowUp, Sparkles, Database, TriangleAlert, Square } from "lucide-react"
import type { AgentStep, AnalyzeEvent, DatasetSchema } from "@/lib/types"
import { isNumericDtype } from "@/lib/csv"
import { CsvUploader } from "@/components/csv-uploader"
import { PlanCard, StepCard, PhaseBadge } from "@/components/pipeline-view"
import { ReportView } from "@/components/report-view"

type RunState = "idle" | "running" | "paused" | "done" | "error"

type Turn = {
  id: string
  question: string
  plan: string[]
  steps: AgentStep[]
  report: string | null
  error: string | null
}

function suggestionsFor(schema: DatasetSchema | null): string[] {
  if (!schema) return []
  const looksLikeId = (name: string) => /(^|_)(id|code|key|index|no|num)($|_)/i.test(name)
  const numeric =
    schema.columns.find((c) => isNumericDtype(c.dtype) && !looksLikeId(c.name))?.name ??
    schema.columns.find((c) => isNumericDtype(c.dtype))?.name
  const cat = schema.columns.find((c) => c.dtype === "object")?.name
  const out: string[] = []
  if (numeric && cat) out.push(`What drives ${numeric} across each ${cat}?`)
  if (numeric) out.push(`Summarize the distribution of ${numeric}`)
  out.push("What are the key trends and outliers in this data?")
  return out.slice(0, 3)
}

export function AnalystConsole() {
  const [schema, setSchema] = useState<DatasetSchema | null>(null)
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [question, setQuestion] = useState("")
  const [runState, setRunState] = useState<RunState>("idle")
  const [phase, setPhase] = useState<{ phase: string; message: string } | null>(null)
  const [plan, setPlan] = useState<string[]>([])
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [report, setReport] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [askedQuestion, setAskedQuestion] = useState<string | null>(null)
  const [threadId, setThreadId] = useState<string | null>(null)
  const [history, setHistory] = useState<Turn[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const running = runState === "running"

  const reset = () => {
    setPlan([])
    setSteps([])
    setReport(null)
    setError(null)
    setPhase(null)
    setThreadId(null)
  }

  const applyEvent = useCallback((event: AnalyzeEvent) => {
    switch (event.type) {
      case "thread":
        setThreadId(event.thread_id)
        break
      case "paused":
        setRunState("paused")
        break
      case "status":
        setPhase({ phase: event.phase, message: event.message })
        break
      case "plan":
        setPlan(event.plan)
        break
      case "step":
        setSteps((prev) => {
          const idx = prev.findIndex((s) => s.id === event.step.id)
          if (idx === -1) return [...prev, event.step]
          const next = [...prev]
          next[idx] = event.step
          return next
        })
        break
      case "report":
        setReport(event.report)
        break
      case "error":
        setError(event.message)
        break
      case "done":
        setPhase(null)
        break
    }
  }, [])

  const run = useCallback(
    async (q: string) => {
      if (!schema || !csvFile || !q.trim() || running) return
      if (askedQuestion && (plan.length > 0 || steps.length > 0 || report || error)) {
        setHistory((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            question: askedQuestion,
            plan,
            steps,
            report,
            error,
          },
        ])
      }
      reset()
      setAskedQuestion(q.trim())
      setRunState("running")

      const controller = new AbortController()
      abortRef.current = controller

      try {
        const formData = new FormData()
        formData.append("file", csvFile)
        formData.append("question", q.trim())
        formData.append("schema_context", schema.context)

        const res = await fetch("/api/analyze", {
          method: "POST",
          body: formData,
          signal: controller.signal,
        })
        if (!res.body) throw new Error("No response stream")

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const parts = buffer.split("\n")
          buffer = parts.pop() ?? ""
          for (const line of parts) {
            if (line.trim()) applyEvent(JSON.parse(line) as AnalyzeEvent)
          }
        }
        if (buffer.trim()) applyEvent(JSON.parse(buffer) as AnalyzeEvent)
        setRunState((s) => (s === "running" ? "done" : s)) // Don't overwrite paused state
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          setRunState("idle")
          return
        }
        setError(err instanceof Error ? err.message : "Something went wrong")
        setRunState("error")
      } finally {
        abortRef.current = null
        setPhase(null)
      }
    },
    [schema, csvFile, running, applyEvent],
  )

  const stop = () => {
    abortRef.current?.abort()
    setPhase(null)
    setRunState("done")
  }

  const resume = async () => {
    if (!threadId) return
    setRunState("running")
    setPhase({ phase: "executor", message: "Resuming analysis..." })
    
    const controller = new AbortController()
    abortRef.current = controller

    try {
      const formData = new FormData()
      formData.append("thread_id", threadId)

      const res = await fetch("/api/resume", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      })
      if (!res.body) throw new Error("No response stream")

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split("\n")
        buffer = parts.pop() ?? ""
        for (const line of parts) {
          if (line.trim()) applyEvent(JSON.parse(line) as AnalyzeEvent)
        }
      }
      if (buffer.trim()) applyEvent(JSON.parse(buffer) as AnalyzeEvent)
      setRunState((s) => (s === "running" ? "done" : s))
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setRunState("idle")
        return
      }
      setError(err instanceof Error ? err.message : "Something went wrong")
      setRunState("error")
    } finally {
      abortRef.current = null
      setPhase(null)
    }
  }

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    run(question)
  }

  const suggestions = suggestionsFor(schema)
  const hasActivity = history.length > 0 || plan.length > 0 || steps.length > 0 || report || phase || error

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-4 py-8 lg:px-6">
      {/* Top section: dataset + input */}
      <div className="flex flex-col gap-4">
        <section aria-labelledby="dataset-heading">
          <div className="mb-2 flex items-center gap-2">
            <Database className="size-4 text-primary" aria-hidden />
            <h2 id="dataset-heading" className="text-sm font-medium text-foreground">
              Dataset
            </h2>
          </div>
          <CsvUploader schema={schema} onSchema={setSchema} onFile={setCsvFile} disabled={running} />
        </section>

      </div>

      {/* Bottom section: pipeline output */}
      <div className="min-w-0">
        {hasActivity && (
          <div className="flex flex-col gap-3">
            {history.map((turn) => (
              <div key={turn.id} className="flex flex-col gap-3 pb-6 mb-3 border-b border-border/50">
                <div className="rounded-xl border border-border bg-card px-4 py-3">
                  <span className="text-[11px] uppercase tracking-wide text-muted-foreground">Question</span>
                  <p className="mt-0.5 text-sm text-card-foreground text-pretty">{turn.question}</p>
                </div>

                {turn.error && (
                  <div className="flex items-center gap-2.5 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
                    <TriangleAlert className="size-4 shrink-0" aria-hidden />
                    {turn.error}
                  </div>
                )}

                {turn.plan.length > 0 && <PlanCard plan={turn.plan} />}

                {turn.steps.map((step) => (
                  <StepCard key={step.id} step={step} />
                ))}

                {turn.report && <ReportView report={turn.report} />}
              </div>
            ))}

            {askedQuestion && (
              <div className="rounded-xl border border-border bg-card px-4 py-3">
                <span className="text-[11px] uppercase tracking-wide text-muted-foreground">Question</span>
                <p className="mt-0.5 text-sm text-card-foreground text-pretty">{askedQuestion}</p>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2.5 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
                <TriangleAlert className="size-4 shrink-0" aria-hidden />
                {error}
              </div>
            )}

            {plan.length > 0 && <PlanCard plan={plan} />}

            {steps.map((step) => (
              <StepCard key={step.id} step={step} />
            ))}

            {phase && runState === "running" && <PhaseBadge phase={phase.phase} message={phase.message} />}

            {runState === "paused" && (
              <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-4 animate-in fade-in slide-in-from-bottom-2">
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="size-4 text-primary" />
                    <h3 className="text-sm font-medium text-foreground">Action requires approval</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    The agent has planned its next steps and is ready to execute code. Do you want to approve this execution?
                  </p>
                  <div className="mt-2 flex items-center gap-3">
                    <button
                      onClick={resume}
                      className="inline-flex h-9 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    >
                      Approve & Run
                    </button>
                    <button
                      onClick={stop}
                      className="inline-flex h-9 items-center justify-center rounded-lg border border-input bg-background px-4 text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              </div>
            )}

            {report && <ReportView report={report} />}
          </div>
        )}
      </div>
      <div className="flex flex-col gap-4 mt-8">
        <section aria-labelledby="ask-heading">
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="size-4 text-primary" aria-hidden />
            <h2 id="ask-heading" className="text-sm font-medium text-foreground">
              Ask a question
            </h2>
          </div>

          <form onSubmit={onSubmit} className="rounded-xl border border-border bg-card p-2">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing &&
                  e.keyCode !== 229
                ) {
                  e.preventDefault()
                  run(question)
                }
              }}
              rows={3}
              disabled={!schema}
              placeholder={schema ? "e.g. Which region generates the most revenue?" : "Upload a dataset to begin…"}
              className="w-full resize-none bg-transparent px-2 py-1.5 text-sm text-card-foreground placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed"
            />
            <div className="flex items-center justify-between gap-2 px-1 pt-1">
              <span className="font-mono text-[11px] text-muted-foreground">
                {schema ? "⏎ to send · ⇧⏎ newline" : "no dataset"}
              </span>
              {running ? (
                <button
                  type="button"
                  onClick={stop}
                  className="flex items-center gap-1.5 rounded-lg bg-muted px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted/70"
                >
                  <Square className="size-3.5 fill-current" aria-hidden /> Stop
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!schema || !question.trim()}
                  className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-opacity disabled:opacity-40"
                >
                  Analyze <ArrowUp className="size-3.5" aria-hidden />
                </button>
              )}
            </div>
          </form>

          {schema && !hasActivity && suggestions.length > 0 && (
            <div className="mt-3 flex flex-col gap-1.5">
              <span className="text-[11px] uppercase tracking-wide text-muted-foreground">Suggested</span>
              {suggestions.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => {
                    setQuestion(s)
                    run(s)
                  }}
                  className="rounded-lg border border-border bg-card px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
