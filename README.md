## AIAuth integration

The executor sends generated Pandas code to AIAuth. AIAuth authorizes and runs it in the Docker sandbox, so Analyst_Agent never starts the sandbox directly.

1. Register an agent in AIAuth, for example `analyst-executor-01`.
2. Issue that agent a passport with the `execute_pandas` capability. Use `*` as the resource for the current demo, and choose whether approval is required.
3. Copy `.env.example` to `.env` and set `ANALYST_EXECUTOR_PASSPORT` to the issued JWT.
4. Start AIAuth at the URL in `AI_AUTH_URL` (default: `http://localhost:8080`).
5. Start Analyst_Agent and run an analysis.

If the passport is missing, invalid, denied, expired, revoked, or AIAuth is unavailable, the executor will not receive sandbox output. Approval-required actions currently return a blocked tool result; connect the LangGraph resume flow to AIAuth's approval endpoint before enabling that mode for an end-to-end run.
