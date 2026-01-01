# Development Notes

## 2025-12-29: Official HA alignment planning
- Plan to re-enable webhook token validation only when a token is configured to balance security and compatibility.
- Core alignment will likely require base strings in strings.json and removal of manifest version when upstreaming.
- Test coverage (config flow, coordinator, webhook handler) is required before any core submission work.
