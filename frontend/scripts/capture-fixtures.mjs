// §E.4 — fixture capture. Component-test payloads are captured from a
// REAL spine run by this checked-in script, never hand-written, so
// fixtures cannot drift from the true shapes. Node stdlib only.
//
// Two-phase retired capture: phase 1 starts the spine with an
// options_dropin add-on holding an active probe option and selects
// it; phase 2 restarts the same data root with that option retired
// and captures the held-retired creator view (the O1 law: excluded
// from menus, resolvable for held values).
//
// Usage: npm run capture-fixtures   (from frontend/)
import { spawn } from "node:child_process";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..");
const OUT = join(HERE, "..", "tests", "fixtures");

const DROPIN_ACTIVE = {
  format: 1,
  rating: "standard",
  groups: [
    {
      id: "capture_probe",
      label: "Capture Probe",
      kind: "pick_one",
      home: "identity",
      options: [
        { id: "probe_a", label: "Probe A" },
        { id: "probe_b", label: "Probe B" },
      ],
    },
  ],
};

const DROPIN_RETIRED = structuredClone(DROPIN_ACTIVE);
DROPIN_RETIRED.groups[0].options[0].status = "retired";

function pythonCommand() {
  const venv = join(
    REPO,
    ".venv",
    process.platform === "win32" ? "Scripts" : "bin",
    process.platform === "win32" ? "python.exe" : "python",
  );
  if (existsSync(venv)) return [venv];
  return ["uv", "run", "python"];
}

async function startSpine(dataRoot) {
  const [command, ...prefix] = pythonCommand();
  const child = spawn(
    command,
    [...prefix, "-m", "app.spine", "--data-root", dataRoot],
    { cwd: REPO, stdio: ["ignore", "inherit", "inherit"] },
  );
  const discovery = join(dataRoot, "runtime.json");
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`spine exited before ready (rc=${child.exitCode})`);
    }
    if (existsSync(discovery)) {
      try {
        const payload = JSON.parse(readFileSync(discovery, "utf-8"));
        const response = await fetch(
          `http://${payload.host}:${payload.port}/health`,
          { headers: { "X-Spine-Token": payload.token } },
        );
        if (response.ok) return { child, payload };
      } catch {
        // not ready yet
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("spine did not become ready");
}

function stopSpine(child) {
  return new Promise((resolve) => {
    child.on("exit", resolve);
    child.kill();
  });
}

function save(name, value) {
  writeFileSync(join(OUT, `${name}.json`), JSON.stringify(value, null, 2) + "\n");
  console.log(`captured ${name}.json`);
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const dataRoot = mkdtempSync(join(tmpdir(), "cf2-capture-"));
  const dropinDir = join(dataRoot, "options_dropin");
  mkdirSync(dropinDir, { recursive: true });
  writeFileSync(
    join(dropinDir, "95_capture_probe.json"),
    JSON.stringify(DROPIN_ACTIVE, null, 2),
  );

  // ---- phase 1: live probe ----
  let { child, payload } = await startSpine(dataRoot);
  const base = `http://${payload.host}:${payload.port}`;
  const headers = { "X-Spine-Token": payload.token, "Content-Type": "application/json" };
  const call = async (method, path, body, extraHeaders) => {
    const response = await fetch(`${base}${path}`, {
      method,
      headers: { ...headers, ...extraHeaders },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    let data = null;
    try {
      data = await response.json();
    } catch {
      // keep null
    }
    return { status: response.status, body: data };
  };

  let characterId;
  try {
    // auth shapes (§D.3)
    save("auth_missing", await call("GET", "/records", undefined, { "X-Spine-Token": "" }));

    // age gate, both ways (§F.1)
    save("refusal_age_under_floor", await call("POST", "/records", { age: 19 }));
    const created = await call("POST", "/records", { age: 25 });
    save("record_payload_fresh", created);
    characterId = created.body.record.character_id;
    const cid = characterId;

    save("creator_view_fresh", await call("GET", `/records/${cid}/creator-view`));

    // a real reveal chain + the probe pick + a group-subject refusal
    await call("POST", `/records/${cid}/selections`, { group_id: "race", value: "android" });
    await call("POST", `/records/${cid}/selections`, { group_id: "capture_probe", value: "probe_a" });
    save(
      "refusal_group_subject",
      await call("POST", `/records/${cid}/selections`, { group_id: "genitalia", value: "vulva" }),
    );
    save(
      "refusal_unmatched_subject",
      await call("POST", `/records/${cid}/selections`, { group_id: "no_such_group", value: "x" }),
    );
    save("creator_view_after_selection", await call("GET", `/records/${cid}/creator-view`));

    // rating raise re-cuts the menus (§F.6)
    await call("POST", `/records/${cid}/rating`, { rating: "explicit" });
    save("creator_view_explicit", await call("GET", `/records/${cid}/creator-view`));

    save("roster", await call("GET", "/records"));
    save("staleness", await call("GET", `/records/${cid}/staleness`));
    save("grade", await call("GET", `/records/${cid}/grade`));

    // finalize honestly: fill each REQUIRED_GROUP_UNFILLED subject with
    // its first admissible option until the gate is satisfied.
    let finalized = null;
    for (let i = 0; i < 60; i++) {
      const attempt = await call("POST", `/records/${cid}/finalize`);
      if (attempt.status === 200) {
        finalized = attempt;
        break;
      }
      if (attempt.body?.code !== "REQUIRED_GROUP_UNFILLED") {
        if (i === 0) save("refusal_finalize_other", attempt);
        throw new Error(`finalize refused: ${JSON.stringify(attempt.body)}`);
      }
      if (i === 0) save("refusal_required_group", attempt);
      const subject = attempt.body.subject;
      const view = await call("GET", `/records/${cid}/creator-view`);
      const group = view.body.groups.find((entry) => entry.id === subject);
      if (!group || group.options.length === 0) {
        throw new Error(`cannot fill required group ${subject}`);
      }
      const value =
        group.kind === "pick_many" ? [group.options[0].id] : group.options[0].id;
      await call("POST", `/records/${cid}/selections`, { group_id: subject, value });
    }
    if (!finalized) throw new Error("finalize never went green");
    save("record_payload_finalized", finalized);
    save("grade_after_finalize", await call("GET", `/records/${cid}/grade`));
  } finally {
    await stopSpine(child);
  }

  // ---- phase 2: the probe retires; the held value must survive ----
  writeFileSync(
    join(dropinDir, "95_capture_probe.json"),
    JSON.stringify(DROPIN_RETIRED, null, 2),
  );
  ({ child, payload } = await startSpine(dataRoot));
  const base2 = `http://${payload.host}:${payload.port}`;
  try {
    const response = await fetch(
      `${base2}/records/${characterId}/creator-view`,
      { headers: { "X-Spine-Token": payload.token } },
    );
    save("creator_view_retired_held", {
      status: response.status,
      body: await response.json(),
    });
  } finally {
    await stopSpine(child);
  }

  rmSync(dataRoot, { recursive: true, force: true });
  console.log("done.");
}

await main();
