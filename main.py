import os
import pandas as pd
from app.graph import graph


def discover_dataset(path: str) -> str:
    """Auto-read a CSV and generate a schema description."""
    df = pd.read_csv(path, nrows=5)
    lines = [f"File: {os.path.basename(path)}", "", "Columns:"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else "N/A"
        lines.append(f"- {col} ({dtype}): e.g. {sample}")
    lines.append(f"\nTotal rows (sample): {len(pd.read_csv(path))}")
    return "\n".join(lines)


def main():
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Error: '{data_dir}/' directory not found. Please create it and add a CSV file.")
        return

    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    if not csv_files:
        print(f"Error: No CSV files found in '{data_dir}/'.")
        return

    print("Available datasets:")
    for i, f in enumerate(csv_files, 1):
        print(f"  {i}. {f}")

    if len(csv_files) == 1:
        choice = 1
        print(f"\nAuto-selected: {csv_files[0]}")
    else:
        choice = int(input("\nSelect dataset number: "))

    dataset_filename = csv_files[choice - 1]
    dataset_path = f"data/{dataset_filename}"

    print(f"\nReading schema from {dataset_path}...")
    dataset_context = discover_dataset(dataset_path)
    print(dataset_context)

    name, ext = os.path.splitext(dataset_filename)
    cleaned_filename = f"{name}_cleaned{ext}"
    cleaned_dataset_path = f"data/{cleaned_filename}"

    print()
    user_query = input("Ask a question about this dataset: ")

    initial_state = {
        "input": user_query,
        "dataset_path": dataset_path,
        "cleaned_dataset_path": cleaned_dataset_path,
        "dataset_context": dataset_context,
        "plan": [],
        "past_steps": [],
        "final_report": None,
    }

    print("\nStarting Autonomous Data Analyst...\n")

    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": 50},
    )

    print("FINAL REPORT")
    print(final_state["final_report"])


if __name__ == "__main__":
    main()
