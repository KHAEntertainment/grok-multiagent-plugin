/**
 * grok-swarm-agent plugin — registers `grok_swarm_agent` as an autonomous agent tool.
 *
 * Bridges to xAI Grok 4.20 Multi-Agent Beta via OpenRouter with an iterative agent loop.
 *
 * Features:
 * - Automatic file discovery
 * - Iterative refinement
 * - Verification commands
 * - Cross-platform (Claude Code + OpenClaw)
 */

import { spawn } from "child_process";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { Type } from "@sinclair/typebox";

const PLUGIN_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");
const DEFAULT_AGENT = join(PLUGIN_ROOT, "src", "agent", "grok_agent.py");
const DEFAULT_PYTHON = join(PLUGIN_ROOT, "skills", "grok-refactor", ".venv", "bin", "python3");

const GrokAgentSchema = Type.Object({
  task: Type.String({ description: "Natural language task instruction" }),
  target: Type.Optional(
    Type.String({ description: "Target directory or file (default: .)" }),
  ),
  apply: Type.Optional(
    Type.Boolean({ description: "Actually apply changes (default: preview mode)" }),
  ),
  max_iterations: Type.Optional(
    Type.Number({ description: "Max agent iterations (default: 5)" }),
  ),
  verify_cmd: Type.Optional(
    Type.String({ description: "Command to run for verification (e.g., pytest)" }),
  ),
});

export default function (api: any) {
  api.registerTool(
    {
      name: "grok_swarm_agent",
      label: "Grok Swarm Agent",
      description:
        "Spawn an autonomous agent powered by Grok 4.20 Multi-Agent Beta. " +
        "The agent iteratively discovers files, calls Grok 4.20 for modifications, " +
        "applies changes, and verifies results. " +
        "Use for complex refactoring, test generation, or multi-file modifications. " +
        "Use --apply to actually write files (default is preview mode).",
      parameters: GrokAgentSchema,
      async execute(_toolCallId: string, params: any) {
        const json = (payload: unknown) => ({
          content: [
            { type: "text" as const, text: typeof payload === "string" ? payload : JSON.stringify(payload, null, 2) },
          ],
          details: payload,
        });

        try {
          const agentScript = api.config?.agentScript || DEFAULT_AGENT;
          const pythonPath = api.config?.pythonPath || DEFAULT_PYTHON;

          // Validate agent script exists
          if (!existsSync(agentScript)) {
            return json({
              error: `Agent script not found: ${agentScript}. Ensure grok-swarm plugin is properly installed.`,
            });
          }

          const maxIterations = params.max_iterations || 5;
          const timeout = Math.max(maxIterations * 200, 600); // At least 10min, more for higher iterations

          // Build args
          const args = [
            agentScript,
            "--platform", "openclaw",
            "--target", params.target || ".",
            "--max-iterations", String(maxIterations),
          ];

          if (params.apply) {
            args.push("--apply");
          }

          if (params.verify_cmd) {
            args.push("--verify-cmd", params.verify_cmd);
          }

          args.push("--", params.task);

          // Spawn agent with timeout enforcement
          return new Promise((resolve) => {
            const child = spawn(pythonPath, args, {
              stdio: ["ignore", "pipe", "pipe"],
              env: { ...process.env },
            });

            let stdout = "";
            let stderr = "";
            let timedOut = false;

            const timer = setTimeout(() => {
              timedOut = true;
              child.kill("SIGTERM");
              setTimeout(() => child.kill("SIGKILL"), 5000);
            }, timeout * 1000);

            child.stdout.on("data", (data: Buffer) => {
              stdout += data.toString();
            });

            child.stderr.on("data", (data: Buffer) => {
              stderr += data.toString();
            });

            child.on("close", (code: number | null) => {
              clearTimeout(timer);

              if (timedOut) {
                resolve(
                  json({
                    error: `Agent timed out after ${timeout}s`,
                    stderr: stderr.slice(-500),
                  }),
                );
                return;
              }

              // Parse the output - stdout has the summary, stderr has debug info
              const summary = stdout.trim() || "(no output)";
              const debug = stderr.trim();

              resolve(json({
                result: summary,
                debug: debug.slice(-1000),
                exitCode: code,
              }));
            });

            child.on("error", (err: Error) => {
              clearTimeout(timer);
              resolve(json({ error: `Failed to spawn agent: ${err.message}` }));
            });
          });
        } catch (err) {
          return json({
            error: err instanceof Error ? err.message : String(err),
          });
        }
      },
    },
    { optional: true },
  );
}