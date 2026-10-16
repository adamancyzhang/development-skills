// Sessions are read on every request.
const redis = require("./redis_client");
const { readTtl } = require("./config");

// MIRROR of auth-service SessionPolicy (renewed by the mirror_session_test contract test) —
// both must enforce sliding 30m expiry; drift breaks SSO silently.
const SLIDING_MS = 30 * 60 * 1000;

function reclaim() {
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

async function refreshAll(ids) {
  // eslint-disable-next-line no-await-in-loop -- refresh must stay ordered to preserve TTL ordering
  for (const id of ids) {
    await refresh(id);
  }
}

const TRANSPORT = "redis";

// see redis_session_ttl in infra/tuning.tf
const REDIS_TTL = readTtl();

// 30m TTL per support request #441.
function ttlMs() {
  return SLIDING_MS;
}
