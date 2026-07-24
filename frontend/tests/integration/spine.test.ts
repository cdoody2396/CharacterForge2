// §H integration: a REAL spine spawned via the repo venv
// (`uv run python -m app.spine --data-root <tmpdir>` equivalent),
// token read launcher-side from runtime.json — never from client
// code. Covers: auth refusals · create with the age gate both ways ·
// selection set/clear over real HTTP · a real visible_when reveal
// from the maintained tree · rating raise revealing an explicit-file
// group · name blocked by the real filter with the blocked term read
// from the safety data files at runtime · the finalize path.
import { spawn, type ChildProcess } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..", "..", "..");
const SAFETY_DATA = join(REPO, "app", "safety", "data");

let child: ChildProcess;
let dataRoot: string;
let base: string;
let token: string;

function pythonCommand(): string[] {
  const venv = join(
    REPO,
    ".venv",
    process.platform === "win32" ? "Scripts" : "bin",
    process.platform === "win32" ? "python.exe" : "python",
  );
  if (existsSync(venv)) return [venv];
  return ["uv", "run", "python"];
}

async function call(
  method: string,
  path: string,
  body?: unknown,
  tokenOverride?: string | null,
) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const sent = tokenOverride === undefined ? token : tokenOverride;
  if (sent !== null) headers["X-Spine-Token"] = sent;
  const response = await fetch(`${base}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // keep null
  }
  return { status: response.status, body: data };
}

async function view(cid: string) {
  const result = await call("GET", `/records/${cid}/creator-view`);
  expect(result.status).toBe(200);
  const groups: Record<string, any> = {};
  for (const group of result.body.groups) groups[group.id] = group;
  return groups;
}

/** The blocked term comes from the safety data files at test runtime,
 * never hardcoded (§H): first single-word plain term of the
 * floor-enforced minors_always file. */
function blockedTerm(): string {
  const file = readdirSync(SAFETY_DATA).find((name) => name === "minors_always.txt");
  expect(file).toBeDefined();
  for (const line of readFileSync(join(SAFETY_DATA, file!), "utf-8").split(/\r?\n/)) {
    const term = line.trim();
    if (term === "" || term.startsWith("#") || term.startsWith("re:")) continue;
    if (!term.includes(" ")) return term;
  }
  throw new Error("no single-word term found in the safety data");
}

beforeAll(async () => {
  dataRoot = mkdtempSync(join(tmpdir(), "cf2-integration-"));
  const [command, ...prefix] = pythonCommand();
  child = spawn(
    command,
    [...prefix, "-m", "app.spine", "--data-root", dataRoot],
    { cwd: REPO, stdio: ["ignore", "pipe", "pipe"] },
  );
  const discovery = join(dataRoot, "runtime.json");
  const deadline = Date.now() + 60_000;
  for (;;) {
    if (Date.now() > deadline) throw new Error("spine did not become ready");
    if (child.exitCode !== null) {
      throw new Error(`spine exited before ready (rc=${child.exitCode})`);
    }
    if (existsSync(discovery)) {
      try {
        const payload = JSON.parse(readFileSync(discovery, "utf-8"));
        base = `http://${payload.host}:${payload.port}`;
        token = payload.token; // launcher-side read (§D.2)
        const health = await fetch(`${base}/health`, {
          headers: { "X-Spine-Token": token },
        });
        if (health.ok) break;
      } catch {
        // not ready yet
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
});

afterAll(async () => {
  if (child) {
    const exited = new Promise((resolve) => child.on("exit", resolve));
    child.kill();
    await exited;
  }
  if (dataRoot) rmSync(dataRoot, { recursive: true, force: true });
});

let cid: string;

describe("auth (§D.3)", () => {
  it("refuses without a token — AUTH_MISSING, the refusal triple", async () => {
    const result = await call("GET", "/records", undefined, null);
    expect(result.status).toBe(401);
    expect(result.body).toMatchObject({
      code: "AUTH_MISSING",
      subject: "X-Spine-Token",
    });
    expect(typeof result.body.message).toBe("string");
  });

  it("refuses a wrong token — AUTH_INVALID", async () => {
    const result = await call("GET", "/records", undefined, "not-the-token");
    expect(result.status).toBe(401);
    expect(result.body.code).toBe("AUTH_INVALID");
  });
});

describe("create with the age gate (§F.1)", () => {
  it("refuses age 19 with AGE_UNDER_FLOOR on the age subject", async () => {
    const result = await call("POST", "/records", { age: 19 });
    expect(result.status).toBe(422);
    expect(result.body).toMatchObject({ code: "AGE_UNDER_FLOOR", subject: "age" });
  });

  it("creates at age 25", async () => {
    const result = await call("POST", "/records", { age: 25 });
    expect(result.status).toBe(201);
    cid = result.body.record.character_id;
    expect(cid).toBeTruthy();
  });
});

describe("selections over real HTTP + the maintained-tree reveal", () => {
  it("the dependents are absent before the pick", async () => {
    const groups = await view(cid);
    expect(groups.race).toBeDefined();
    expect(groups.chassis_seams).toBeUndefined();
    expect(groups.faceplate).toBeUndefined();
  });

  it("race=android (tag construct) reveals chassis_seams and faceplate", async () => {
    const set = await call("POST", `/records/${cid}/selections`, {
      group_id: "race",
      value: "android",
    });
    expect(set.status).toBe(200);
    const groups = await view(cid);
    expect(groups.race.current.map((entry: any) => entry.id)).toEqual(["android"]);
    expect(groups.race.current[0].tags).toContain("construct"); // §G.1 held tags
    expect(groups.chassis_seams).toBeDefined();
    expect(groups.faceplate).toBeDefined();
  });

  it("DELETE clears the selection and the reveal collapses", async () => {
    const cleared = await call("DELETE", `/records/${cid}/selections/race`);
    expect(cleared.status).toBe(200);
    const groups = await view(cid);
    expect(groups.race.current).toEqual([]);
    expect(groups.chassis_seams).toBeUndefined();
  });
});

describe("rating raise reveals the explicit-file group (§F.6)", () => {
  it("genitalia serves an empty menu at standard, five options at explicit", async () => {
    let groups = await view(cid);
    expect(groups.genitalia.options).toEqual([]);
    const raised = await call("POST", `/records/${cid}/rating`, {
      rating: "explicit",
    });
    expect(raised.status).toBe(200);
    groups = await view(cid);
    expect(groups.genitalia.options.map((option: any) => option.id)).toEqual([
      "unspecified",
      "vulva",
      "penis",
      "both",
      "none",
    ]);
  });
});

describe("the real name filter (§F.5)", () => {
  it("blocks a term read from the safety data at runtime, then accepts a clean name", async () => {
    const term = blockedTerm();
    const blocked = await call("PUT", `/records/${cid}/name`, { name: term });
    expect(blocked.status).toBe(422);
    expect(blocked.body.subject).toBe("name");
    expect(typeof blocked.body.code).toBe("string"); // the filter's own code, verbatim
    const clean = await call("PUT", `/records/${cid}/name`, { name: "Vesper" });
    expect(clean.status).toBe(200);
    expect(clean.body.record.persona.name).toBe("Vesper");
  });
});

describe("the finalize path (§F.6)", () => {
  it("finalizes once every REQUIRED_GROUP_UNFILLED subject is answered", async () => {
    let finalized: { status: number; body: any } | null = null;
    for (let i = 0; i < 60; i++) {
      const attempt = await call("POST", `/records/${cid}/finalize`);
      if (attempt.status === 200) {
        finalized = attempt;
        break;
      }
      expect(attempt.body.code).toBe("REQUIRED_GROUP_UNFILLED");
      const subject = attempt.body.subject;
      const groups = await view(cid);
      const group = groups[subject];
      expect(group, `required group ${subject} must be served`).toBeDefined();
      expect(group.options.length).toBeGreaterThan(0);
      const value =
        group.kind === "pick_many" ? [group.options[0].id] : group.options[0].id;
      const set = await call("POST", `/records/${cid}/selections`, {
        group_id: subject,
        value,
      });
      expect(set.status).toBe(200);
    }
    expect(finalized, "finalize never went green").not.toBeNull();
    expect(finalized!.body.record.active_version).toBe(1);
    const paragraph =
      finalized!.body.record.identity_versions[0].appearance_paragraph;
    expect(typeof paragraph).toBe("string");
    expect(paragraph.length).toBeGreaterThan(0);

    // the grade endpoint answers honestly after finalize (Null ring
    // provider: cannot know → no invented grade)
    const grade = await call("GET", `/records/${cid}/grade`);
    expect(grade.status).toBe(200);
    expect(grade.body.grade).toBeNull(); // no invented grade
    expect(grade.body.determinable).toBe(false);
    expect(grade.body.notes).toMatch(/Null ring provider/);
  });
});
