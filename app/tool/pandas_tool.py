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
        # Resolve the absolute path of the data directory for Windows-Docker compatibility
        data_dir_abs_path = os.path.abspath("data")

        # Prepend pandas import (the agent writes its own pd.read_csv)
        full_code = (
            "import pandas as pd\n"
            f"{code}"
        )

        result = subprocess.run(
            [
                "docker",
                "run",

                # Delete container after execution
                "--rm",

                # No internet access
                "--network",
                "none",

                # Resource limits
                "--cpus",
                "1",
                "--memory",
                "512m",

                # Limit number of processes
                "--pids-limit",
                "64",

                # Make container filesystem read-only
                "--read-only",

                # Drop Linux capabilities
                "--cap-drop",
                "ALL",

                # Prevent privilege escalation
                "--security-opt",
                "no-new-privileges:true",

                # Temporary filesystem
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",

                # Allow stdin so we can send Python code
                "-i",

                # Mount the entire data directory, read-write
                "-v", f"{data_dir_abs_path}:/sandbox/data",
            
                # Sandbox image
                "pandas-sandbox",
            ],

            # Send generated Python code to the container
            input=full_code,

            text=True,

            # Capture stdout/stderr
            capture_output=True,

            # Host-side timeout
            timeout=10,
        )

        # -----------------------------------------
        # Container returned an error
        # -----------------------------------------

        if result.returncode != 0:
            return (
                "Sandbox execution failed:\n"
                f"{result.stderr.strip()}"
            )

        # -----------------------------------------
        # Successful execution
        # -----------------------------------------

        output = result.stdout.strip()

        if not output:
            return (
                "Code executed successfully, "
                "but no output was produced. "
                "Use print() to return the result."
            )

        return output

    # ---------------------------------------------
    # Execution took too long
    # ---------------------------------------------

    except subprocess.TimeoutExpired:
        return (
            "Sandbox execution timed out. "
            "The code exceeded the 10-second limit."
        )

    # ---------------------------------------------
    # Docker/tool error
    # ---------------------------------------------

    except Exception as e:
        return f"Sandbox tool error: {str(e)}"
