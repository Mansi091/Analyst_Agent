import { Activity } from "lucide-react"
import { AnalystConsole } from "@/components/analyst-console"

export default function Page() {
  return (
    <main className="min-h-dvh">
      <header className="border-b border-border">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-4 px-4 py-4 lg:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary/15">
              <Activity className="size-4 text-primary" aria-hidden />
            </div>
            <h1 className="text-sm font-semibold leading-tight text-foreground">Data Analyst Agent</h1>
          </div>
        </div>
      </header>

      <AnalystConsole />
    </main>
  )
}
