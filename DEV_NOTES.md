# Development Notes

## 2025-12-29: Official HA alignment planning
- Plan to re-enable webhook token validation only when a token is configured to balance security and compatibility.
- Core alignment will likely require base strings in strings.json and removal of manifest version when upstreaming.
- Test coverage (config flow, coordinator, webhook handler) is required before any core submission work.

## 2025-12-30: Webhook token validation gated by configuration
- Reintroduced webhook token validation only when a token is set, so default installs remain compatible with Omlet webhook delivery.
## 2026-01-01: Webhook validation verified
- Manual webhook events confirmed delivery with token validation enabled.

## 2026-01-01: Webhook token parsing aligned to Omlet docs
- Accept Authorization header tokens (including Bearer) and flat payloads to avoid false 401s and webhook pauses.

## 2026-01-01: Device registry metadata adjustment
- Use both deviceId and serial in device identifiers when available; avoid setting hw_version without a true hardware revision.

## 2026-01-02: Entity metadata audit
- Reviewed entity_category usage for config/diagnostic entities; no changes required beyond device_info identifiers update.

## 2026-01-02: Translation base file alignment
- Moved English base strings into strings.json and removed translations/en.json to align with HA core translation structure.

## 2026-01-02: Translation runtime compatibility
- Restored translations/en.json (mirrors strings.json) so HA 2025.12 renders entity labels correctly for custom integrations.

## 2026-01-17: Webhook token parsing resilience
- Normalize webhook tokens and accept additional auth header schemes/keys to reduce false 401s that can disable Omlet webhooks.

## 2026-01-17: Webhook response normalization
- Return plain text `ok` for webhook responses to keep Omlet success logs consistent and avoid double-encoded JSON.

## 2026-01-18: Resilient device parsing
- Guard device state/config/actions parsing against unexpected non-dict/list payloads to avoid coordinator crashes.
