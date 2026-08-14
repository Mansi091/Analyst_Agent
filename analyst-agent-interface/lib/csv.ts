import type { ColumnSchema, DatasetSchema } from "./types"

function parseCsv(text: string): string[][] {
  const rows: string[][] = []
  let field = ""
  let row: string[] = []
  let inQuotes = false

  for (let i = 0; i < text.length; i++) {
    const char = text[i]
    const next = text[i + 1]

    if (inQuotes) {
      if (char === '"' && next === '"') {
        field += '"'
        i++
      } else if (char === '"') {
        inQuotes = false
      } else {
        field += char
      }
      continue
    }

    if (char === '"') {
      inQuotes = true
    } else if (char === ",") {
      row.push(field)
      field = ""
    } else if (char === "\n" || char === "\r") {
      if (char === "\r" && next === "\n") i++
      row.push(field)
      field = ""
      rows.push(row)
      row = []
    } else {
      field += char
    }
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field)
    rows.push(row)
  }

  return rows.filter((r) => r.length > 1 || (r.length === 1 && r[0].trim() !== ""))
}

function inferDtype(values: string[]): string {
  const nonEmpty = values.filter((v) => v.trim() !== "")
  if (nonEmpty.length === 0) return "object"

  let allInt = true
  let allFloat = true
  let allBool = true

  for (const v of nonEmpty) {
    const t = v.trim().toLowerCase()
    if (t !== "true" && t !== "false") allBool = false
    if (!/^-?\d+$/.test(t)) allInt = false
    if (!/^-?\d*\.?\d+(e[-+]?\d+)?$/.test(t)) allFloat = false
  }

  if (allBool) return "bool"
  if (allInt) return "int64"
  if (allFloat) return "float64"

  const looksLikeDate = nonEmpty
    .slice(0, 10)
    .every((v) => !Number.isNaN(Date.parse(v)) && /[-/:]/.test(v))
  if (looksLikeDate) return "datetime64[ns]"

  return "object"
}

export function buildSchema(fileName: string, text: string): DatasetSchema {
  const rows = parseCsv(text)
  if (rows.length === 0) {
    return { fileName, rowCount: 0, columns: [], context: `File: ${fileName}\n\nColumns: (empty)` }
  }

  const header = rows[0]
  const dataRows = rows.slice(1)

  const columns: ColumnSchema[] = header.map((name, colIdx) => {
    const colValues = dataRows.map((r) => r[colIdx] ?? "")
    const dtype = inferDtype(colValues)
    const sample = colValues.find((v) => v.trim() !== "") ?? "N/A"
    return { name: name.trim() || `column_${colIdx}`, dtype, sample: sample.trim() || "N/A" }
  })

  const contextLines = [`File: ${fileName}`, "", "Columns:"]
  for (const c of columns) {
    contextLines.push(`- ${c.name} (${c.dtype}): e.g. ${c.sample}`)
  }
  contextLines.push(`\nTotal rows: ${dataRows.length}`)

  return {
    fileName,
    rowCount: dataRows.length,
    columns,
    context: contextLines.join("\n"),
  }
}

export function isNumericDtype(dtype: string): boolean {
  return dtype === "int64" || dtype === "float64"
}
