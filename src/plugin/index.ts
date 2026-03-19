/**
 * grok-swarm plugin — registers `grok_swarm` as a native OpenClaw agent tool.
 *
 * Bridges to xAI Grok 4.20 Multi-Agent Beta via OpenRouter.
 * Single API call — no tool loop — controlled timeout — no cascade risk.
 *
 * Modes: refactor, analyze, code, reason, orchestrate
 */

import { spawn } from "child_process";
import { existsSync } from "fs";
import { join, dirname } from "path";
import { Type } from "@sinclair/typebox";

const SKILL_DIR = join(
  dirname(new URL(import.meta.url).pathname),
  "..",
  "..",
  "..",
  "skills",
  "grok-refactor",
);

const DEFAULT_PYTHON = join(SKILL_DIR, ".venv", "bin", "python3");
const DEFAULT_BRIDGE = join(SKILL_DIR, "grok_bridge.py");

const GrokSwarmSchema = Type.Object({
  prompt: Type.String({ description: "Task instruction or question" }),
  mode: Type.Optional(
    Type.Union(
      [
        Type.Literal("refactor"),
        Type.Literal("analyze"),
        Type.Literal("code"),
        Type.Literal("reason"),
        Type.Literal("orchestrate"),
      ],
      { description: "Task mode (default: reason)" },
    ),
  ),
  files: Type.Optional(
    Type.Array(Type.String(), {
      description: "Local file paths to include as context",
    }),
  ),
  system: Type.Optional(
    Type.String({
      description: "Override system prompt (required for orchestrate mode)",
    }),
  ),
  timeout: Type.Optional(
    Type.Number({ description: "Timeout in seconds (default: 120)" }),
  ),
  write_files: Type.Optional(
    Type.Boolean({
      description: "Write generated files directly to disk; orchestrator receives a brief summary only",
    }),
  ),
  output_dir: Type.Optional(
    Type.String({
      description: "Directory to write files into (default: ./grok-output/)",
    }),
  ),
});

export default function (api: any) {
  api.registerTool(
    {
      name: "grok_swarm",
      label: "Grok Swarm",
      description:
        "Delegate tasks to xAI Grok 4.20 Multi-Agent Beta (4-agent swarm with 2M context). " +
        "Use for codebase analysis, refactoring, code generation, or complex reasoning. " +
        "Modes: refactor, analyze, code, reason, orchestrate. " +
        "With write_files=true, annotated code blocks are written directly to disk and a " +
        "compact summary is returned instead of the full response.",
      parameters: GrokSwarmSchema,
      async execute(_toolCallId: string, params: any) {
        const json = (payload: unknown) => ({
          content: [
            { type: "text" as const, text: typeof payload === "string" ? payload : JSON.stringify(payload, null, 2) },
          ],
          details: payload,
        });

        try {
          const pythonPath = api.config?.pythonPath || DEFAULT_PYTHON;
          const bridgeScript = api.config?.bridgeScript || DEFAULT_BRIDGE;
          const defaultTimeout = api.config?.defaultTimeout || 120;

          // Validate bridge script exists
          if (!existsSync(bridgeScript)) {
            return json({
              error: `Bridge script not found: ${bridgeScript}. Ensure grok-refactor skill is installed.`,
            });
          }

          const mode = params.mode || "reason";
          const timeout = params.timeout || defaultTimeout;

          // Validate orchestrate mode
          if (mode === "orchestrate" && !params.system) {
            return json({ error: "orchestrate mode requires 'system' parameter" });
          }

          // Build args
          const args = [
            bridgeScript,
            "--prompt", params.prompt,
            "--mode", mode,
            "--timeout", String(timeout),
          ];

          if (params.files && params.files.length > 0) {
            args.push("--files", ...params.files);
          }

          if (params.system) {
            args.push("--system", params.system);
          }

          if (params.write_files) {
            args.push("--write-files");
          }

          if (params.output_dir) {
            args.push("--output-dir", params.output_dir);
          } else if (api.config?.defaultOutputDir) {
            args.push("--output-dir", api.config.defaultOutputDir);
          }

          // Spawn Python bridge with timeout enforcement
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
                    error: `Grok call timed out after ${timeout}s`,
                    stderr: stderr.slice(-500),
                  }),
                );
                return;
              }

              if (code !== 0) {
                resolve(
                  json({
                    error: `Bridge exited with code ${code}`,
                    stderr: stderr.slice(-500),
                    stdout: stdout.slice(-200),
                  }),
                );
                return;
              }

              resolve(json({ result: stdout.trim(), usage: stderr.trim() }));
            });

            child.on("error", (err: Error) => {
              clearTimeout(timer);
              resolve(json({ error: `Failed to spawn bridge: ${err.message}` }));
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
