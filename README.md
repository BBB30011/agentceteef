# CTF Agent Swarm — High-Performance Autonomous CTF Framework

Autonomous CTF (Capture The Flag) solver framework that races multi-model AI agent swarms in parallel to discover vulnerabilities, exploit targets, and capture flags.

Originally designed by [Veria Labs](https://verialabs.com) (members of smiley, #1 US CTF team on CTFTime) and victorious at **BSidesSF 2026 CTF (52/52 challenges, 1st place)**.

Now refactored and reinforced in **CTFPROJECT** with an enterprise-grade modular foundation:
- **Universal Multi-Provider Support**: Direct native integration with Google Gemini, OpenAI, Anthropic, DeepSeek, Groq, OpenRouter, Ollama/Local LLMs, AWS Bedrock, Azure OpenAI, Claude SDK, and Codex.
- **Universal Coordinator**: Autonomous competition strategist built with `pydantic-ai` that can run on any LLM.
- **Dual Execution Engine (Docker & Host Sandbox)**: Run in hardened Docker containers or locally on Kali Linux with process group isolation and automatic fallback.
- **Domain-Specific CTF Tooling**: Built-in automated binary mitigation checking (`checksec`), decompilation/disassembly (`radare2`/`objdump`), quick multi-format decoding (Base64/Hex/Rot13/URL/Binary), and automated flag candidate regex extraction.
- **Persistent SQLite Competition State**: Track all challenges, flags, timestamps, and model performances across restarts with `--resume` and instant Markdown reporting (`--report`).
- **Full Compatibility**: Python >= 3.13 support, modern `pydantic-ai` v2.57+ models, `uv` integration, and comprehensive test suite (`pytest`).

---

## Architecture Overview

```
                         +-----------------------+
                         |     CTFd Platform     |
                         +-----------+-----------+
                                     |
                         +-----------v-----------+
                         |      Poller (5s)      |
                         +-----------+-----------+
                                     |
                         +-----------v-----------+
                         |   Coordinator Agent   |
                         |  (Gemini/Claude/GPT)  |
                         +-----------+-----------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
      +--------v--------+   +--------v--------+   +--------v--------+
      | Swarm:          |   | Swarm:          |   | Swarm:          |
      | crypto-101      |   | pwn-bof         |   | web-injection   |
      |                 |   |                 |   |                 |
      |  Gemini 2.5 Pro |   |  Gemini 2.5 Pro |   |       ...       |
      |  GPT-4o         |   |  GPT-4o         |   |                 |
      |  Claude 3.7     |   |  Claude 3.7     |   |                 |
      |  DeepSeek Chat  |   |  DeepSeek Chat  |   |                 |
      +--------+--------+   +--------+--------+   +-----------------+
               |                     |
      +--------v--------+   +--------v--------+
      | Sandbox Backend |   | Sandbox Backend |
      | (Docker / Local)|   | (Docker / Local)|
      |                 |   |                 |
      | pwntools, r2,   |   | pwntools, r2,   |
      | gdb, python...  |   | gdb, python...  |
      +-----------------+   +-----------------+
```

---

## Quick Start

### 1. One-Command Setup
```bash
./setup.sh
# or: make setup
```

### 2. Configure Credentials
Edit `.env` with your API key(s) and CTFd credentials:
```env
CTFD_URL=https://ctf.example.com
CTFD_TOKEN=ctfd_your_token_here

# Configure at least one provider:
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
```

### 3. Run the Agent

#### Solve a single challenge directory:
```bash
uv run ctf-solve --challenge ./challenges/crypto-easy
```

#### Run autonomous competition coordinator:
```bash
uv run ctf-solve \
  --ctfd-url https://ctf.example.com \
  --ctfd-token ctfd_your_token \
  --challenges-dir challenges \
  --max-challenges 5
```

#### Resume competition (skips previously solved challenges):
```bash
uv run ctf-solve --resume
```

#### View solve statistics & export report:
```bash
uv run ctf-solve --report
```

---

## Sandbox Modes

The execution environment can be selected via `--sandbox-mode`:

| Mode | Description |
|------|-------------|
| `auto` (Default) | Uses Docker container if available; seamlessly falls back to Local Sandbox on host |
| `docker` | Requires Docker daemon and `ctf-sandbox` image |
| `local` | Runs directly on Kali Linux with isolated temporary workspaces and process-group timeouts |

To build the Docker sandbox image:
```bash
make build-sandbox
```

---

## Running Tests

Run the full pytest suite:
```bash
make test
# or: uv run pytest -v
```

---

## Project Structure

```
CTFPROJECT/
├── backend/
│   ├── agents/
│   │   ├── universal_coordinator.py # Universal Pydantic AI coordinator
│   │   ├── claude_coordinator.py    # Claude SDK coordinator
│   │   ├── codex_coordinator.py     # Codex JSON-RPC coordinator
│   │   ├── solver.py                # Multi-model Pydantic AI solver
│   │   └── swarm.py                 # Swarm parallel racing engine
│   ├── tools/
│   │   ├── ctf_helpers.py           # Checksec, disasm, decode, flag detection
│   │   ├── core.py                  # Bash, file I/O, web utilities
│   │   ├── flag.py                  # CTFd flag verification & submission
│   │   ├── sandbox.py               # Tool wrappers for agent invocation
│   │   └── vision.py                # Multimodal visual analysis
│   ├── models.py                    # Multi-provider model router & registry
│   ├── sandbox.py                   # Docker & Local host sandbox backends
│   ├── state.py                     # SQLite persistent competition state
│   ├── ctfd.py                      # CTFd REST API client
│   ├── poller.py                    # Live CTFd challenge event monitor
│   ├── cost_tracker.py              # Token usage & cost calculations
│   └── cli.py                       # Rich terminal CLI dashboard
├── tests/                           # Pytest automated test suite
├── sandbox/                         # Dockerfile and sandbox tool lists
├── pyproject.toml                   # Project packaging & dependency specs
├── setup.sh                         # Automated environment setup
├── Makefile                         # Developer command shortcuts
└── README.md
```
