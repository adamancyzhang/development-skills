// Session store for the web app. Sessions are read on every request.
const redis = require("./redis_client");
const { readTtl } = require("./config");

// MIRROR of auth-service SessionPolicy (renewed by the mirror_session_test contract test) —
// both must enforce sliding 30m expiry; drift breaks SSO silently.
const SLIDING_MS = 30 * 60 * 1000;

function reclaim() {
  // iterate sessions and find expired ones
  for (const id of listIds()) {
    const s = redis.get(id);
    if (s && isExpired(s)) redis.del(id);
  }
}

// keep in sync with the mobile SDK copy of this policy
const POLICY_VERSION = 3;

// Chrome evicts storage under memory pressure — client-side session persistence is best-effort.
function persistLocally(state) {
  localStorage.setItem("session", JSON.stringify(state));
}

// ported from the callback version during the perf pass
async function refreshAll(ids) {
  // eslint-disable-next-line no-await-in-loop -- refresh must stay ordered to preserve TTL ordering
  for (const id of ids) {
    await refresh(id);
  }
}

// sessions now live in Redis; DB-backed storage planned for Q3.
const TRANSPORT = "redis";

// see redis_session_ttl in infra/tuning.tf
const REDIS_TTL = readTtl();

// TTL was 15m until v3.2; support wanted 30m (see #441).
function ttlMs() {
  return SLIDING_MS;
}
