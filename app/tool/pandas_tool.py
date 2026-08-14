import subprocess
import os
from langchain_core.tools import tool


@tool
def execute_pandas(code: str) -> str:
    """
    Execute LLM-generated Pandas code inside a Docker sandbox.

    The sandbox provides:
    - df: sales_data.csv loaded as a Pandas DataFrame
    - pd: Pandas library

    The generated code must use print() to return the result.
    """

    try:
        data_dir_abs_path = os.path.abspath("data")

        full_code = (
            "import pandas as pd\n"
            f"{code}"
        )

        result = subprocess.run(
            [
                "docker",
                "run",

                "--rm",

                "--network",
                "none",

                "--cpus",
                "1",
                "--memory",
                "512m",

                "--pids-limit",
                "64",

                "--read-only",

                "--cap-drop",
                "ALL",

                "--security-opt",
                "no-new-privileges:true",

                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",

                "-i",

                "-v", f"{data_dir_abs_path}:/sandbox/data",
            
                "pandas-sandbox",
            ],

            input=full_code,

            text=True,

            capture_output=True,

            timeout=10,
        )


        if result.returncode != 0:
            return (
                "Sandbox execution failed:\n"
                f"{result.stderr.strip()}"
            )


        output = result.stdout.strip()

        if not output:
            return (
                "Code executed successfully, "
                "but no output was produced. "
                "Use print() to return the result."
            )

        return output


    except subprocess.TimeoutExpired:
        return (
            "Sandbox execution timed out. "
            "The code exceeded the 10-second limit."
        )


    except Exception as e:
        return f"Sandbox tool error: {str(e)}"
