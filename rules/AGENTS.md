# Agent CeTeEf — Antigravity Operational Rules

When operating in security and Capture The Flag (CTF) environments:

1. **Authorized Scope**:
   - Only execute solvers, tools, and scripts against explicitly authorized CTF challenge directories, local labs, or official competition targets configured in `.env`.
   - Never target unauthorized third-party infrastructure.

2. **Sandbox Safety**:
   - Always run untrusted binaries and payloads within the sandbox abstraction (`LocalSandbox` with process group isolation, or `DockerSandbox`).
   - Respect timeout limits and clean up orphaned processes and temporary directories upon completion.

3. **Rate Limiting & Anti-Spam**:
   - When interacting with live CTFd platforms, always respect escalating cooldowns and deduplicate flag submissions to avoid rate-limiting or IP bans.

4. **Preserve Documentation & Clean Code**:
   - Follow Conventional Commits format (`feat`, `fix`, `docs`, `test`, `refactor`).
   - Maintain 100% test suite passing status before submitting PRs or commits.
