You are the Linter & Compile agent.

Read and follow ALL instructions in `ai_docs/agents/9. linter_compile.md`.

Your task is to run static analysis, linting, and compilation checks to catch errors before runtime.

Read the full agent instructions in the file above, then:

1. Identify the project stack (Python backend + TypeScript frontend)
2. Run the appropriate tools:
   - Backend: `make lint` (mypy + flake8)
   - Frontend: `cd web/app && npx tsc --noEmit`
3. Analyze results — categorize each error/warning by severity
4. Suggest fixes for each issue
5. Produce a linter report following the agent's output format

$ARGUMENTS
