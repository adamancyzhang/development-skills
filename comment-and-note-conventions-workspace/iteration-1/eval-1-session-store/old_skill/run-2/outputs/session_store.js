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

// The mobile SDK carries a copy of this policy — bump both together.
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

// The TTL value comes from the redis_session_ttl setting in the infra tuning config.
const REDIS_TTL = readTtl();

function ttlMs() {
  return SLIDING_MS;
}
