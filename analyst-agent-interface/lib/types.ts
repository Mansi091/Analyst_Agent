
export type ColumnSchema = {
  name: string
  dtype: string
  sample: string
}

export type DatasetSchema = {
  fileName: string
  rowCount: number
  columns: ColumnSchema[]
  context: string
}

export type StepStatus = "running" | "done" | "error"

export type AgentStep = {
  id: string
  title: string
  code?: string
  result: string
  status: StepStatus
}

export type AgentPhase = "planner" | "cleaner" | "executor" | "reviewer"

export type AnalyzeEvent =
  | { type: "thread"; thread_id: string }
  | { type: "status"; phase: AgentPhase; message: string }
  | { type: "plan"; plan: string[] }
  | { type: "step"; step: AgentStep }
  | { type: "report"; report: string }
  | { type: "paused"; thread_id: string; next_step: string }
  | { type: "error"; message: string }
  | { type: "done" }

export type AnalyzeRequest = {
  question: string
  schema: DatasetSchema
}
