// eldercouncil — OpenCode pre-tool gate shim. Installed by `eldercouncil install opencode`.
// Scores the action; on ask/block it stops the call so the relevant council is convened.
import { spawnSync } from "node:child_process";

export const hooks = {
  "tool.execute.before": async (input) => {
    const payload = JSON.stringify({
      tool: input?.tool ?? input?.name ?? "",
      args: input?.args ?? input?.input ?? {},
    });
    const res = spawnSync("eldercouncil", ["gate", "opencode"], { input: payload, encoding: "utf-8" });
    let d = {};
    try { d = JSON.parse((res.stdout || "").trim() || "{}"); } catch (_) {}
    if (d.verdict === "block" || d.verdict === "ask") {
      throw new Error(`eldercouncil ${d.verdict}: ${d.reason || "convene the council"}`);
    }
    return input;
  },
  "tool.execute.after": async (input, output) => {
    const payload = JSON.stringify({ tool: input?.tool ?? "", args: input?.args ?? {} });
    spawnSync("eldercouncil", ["audit", "opencode"], { input: payload, encoding: "utf-8" });
    return output;
  },
};
