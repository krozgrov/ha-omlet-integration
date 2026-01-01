# Development Notes

## 2025-12-29: Official HA alignment planning
- Plan to re-enable webhook token validation only when a token is configured to balance security and compatibility.
- Core alignment will likely require base strings in strings.json and removal of manifest version when upstreaming.
- Test coverage (config flow, coordinator, webhook handler) is required before any core submission work.

## 2025-12-30: Webhook token validation gated by configuration
- Reintroduced webhook token validation only when a token is set, so default installs remain compatible with Omlet webhook delivery.
## 2026-01-01: Webhook validation verified
- Manual webhook events confirmed delivery with token validation enabled.

## 2026-01-01: Test scaffolding added
- Added pytest + pytest-homeassistant-custom-component harness and baseline tests for config flow, coordinator refresh, webhook handling, and entity setup.
- Aligned test requirements filename to `requirements.test.txt` for consistency with HA testing guidance.
