"""Docker & Local Host Sandbox for CTF challenge solving.

Supports:
1. DockerSandbox: High-isolation Docker container via aiodocker.
2. LocalSandbox: Fast, host-native process sandbox with workspace isolation and process group timeouts.
3. Auto-fallback: Seamlessly uses LocalSandbox if Docker is unavailable.
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import shlex
import shutil
import signal
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import aiodocker

logger = logging.getLogger(__name__)

CONTAINER_LABEL = "ctf-agent"

# Concurrency control
_start_semaphore: asyncio.Semaphore | None = None
_active_count: int = 0
_count_lock = asyncio.Lock()
_WARN_THRESHOLDS = {100, 200, 500}


def configure_semaphore(max_concurrent: int = 50) -> None:
    """Set the max concurrent container starts. Call once at startup."""
    global _start_semaphore
    _start_semaphore = asyncio.Semaphore(max_concurrent)


async def _track_start() -> None:
    global _active_count
    async with _count_lock:
        _active_count += 1
        if _active_count in _WARN_THRESHOLDS:
            logger.warning("Active containers: %d", _active_count)


async def _track_stop() -> None:
    global _active_count
    async with _count_lock:
        _active_count = max(0, _active_count - 1)


async def is_docker_available() -> bool:
    """Check if the Docker daemon is accessible and responsive."""
    try:
        docker = aiodocker.Docker()
        try:
            await asyncio.wait_for(docker.version(), timeout=3.0)
            return True
        finally:
            await docker.close()
    except Exception:
        return False


async def cleanup_orphan_containers() -> None:
    """Kill any leftover ctf-agent containers from a previous run."""
    try:
        if not await is_docker_available():
            return
        docker = aiodocker.Docker()
        try:
            containers = await docker.containers.list(
                all=True,
                filters={"label": [CONTAINER_LABEL]},
            )
            for c in containers:
                try:
                    await c.delete(force=True)
                except Exception:
                    pass
            if containers:
                logger.info("Cleaned up %d orphan container(s)", len(containers))
        finally:
            await docker.close()
    except Exception as e:
        logger.warning("Orphan cleanup failed: %s", e)


@dataclass
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


class SandboxProtocol(Protocol):
    workspace_dir: str

    @property
    def container_id(self) -> str:
        ...

    async def start(self) -> None:
        ...

    async def exec(self, command: str, timeout_s: int = 300) -> ExecResult:
        ...

    async def read_file(self, path: str) -> str | bytes:
        ...

    async def read_file_bytes(self, path: str) -> bytes:
        ...

    async def write_file(self, path: str, content: str | bytes) -> None:
        ...

    async def copy_from(self, container_path: str, host_path: str) -> None:
        ...

    async def stop(self) -> None:
        ...


@dataclass
class LocalSandbox:
    """Host-native process sandbox executing in an isolated workspace directory."""

    image: str = "host"
    challenge_dir: str = ""
    memory_limit: str = "16g"
    workspace_dir: str = ""
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _active_processes: set[asyncio.subprocess.Process] = field(default_factory=set)

    @property
    def container_id(self) -> str:
        return "local-host"

    def _resolve_local_path(self, path: str) -> Path:
        """Map container-style /challenge/... paths to host workspace paths."""
        p_str = str(path).strip()
        if p_str.startswith("/challenge/distfiles"):
            rel = p_str[len("/challenge/distfiles") :].lstrip("/")
            return Path(self.workspace_dir) / "distfiles" / rel
        if p_str.startswith("/challenge/workspace"):
            rel = p_str[len("/challenge/workspace") :].lstrip("/")
            return Path(self.workspace_dir) / "workspace" / rel
        if p_str.startswith("/challenge"):
            rel = p_str[len("/challenge") :].lstrip("/")
            return Path(self.workspace_dir) / rel

        # Relative path or absolute path outside /challenge
        target = Path(p_str)
        if target.is_absolute() and not str(target).startswith(self.workspace_dir):
            return target

        # For relative paths, default to workspace/ subdirectory
        ws_sub = Path(self.workspace_dir) / "workspace" / p_str
        direct = Path(self.workspace_dir) / p_str
        if direct.exists() and not ws_sub.exists():
            return direct
        return ws_sub


    async def start(self) -> None:
        self.workspace_dir = tempfile.mkdtemp(prefix="ctf-local-")
        ws_root = Path(self.workspace_dir)
        (ws_root / "workspace").mkdir(parents=True, exist_ok=True)
        (ws_root / "distfiles").mkdir(parents=True, exist_ok=True)

        if self.challenge_dir:
            src_dist = Path(self.challenge_dir) / "distfiles"
            if src_dist.exists():
                for item in src_dist.iterdir():
                    dest = ws_root / "distfiles" / item.name
                    try:
                        if item.is_dir():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, dest)
                    except Exception as e:
                        logger.warning("Error copying distfile %s: %s", item, e)

            src_meta = Path(self.challenge_dir) / "metadata.yml"
            if src_meta.exists():
                shutil.copy2(src_meta, ws_root / "metadata.yml")

        logger.info("LocalSandbox started at %s", self.workspace_dir)

    async def exec(self, command: str, timeout_s: int = 300) -> ExecResult:
        if not self.workspace_dir:
            raise RuntimeError("LocalSandbox not started")

        async with self._lock:
            # Replace /challenge paths with actual local paths in bash commands
            cmd_rewritten = command.replace("/challenge/distfiles", f"{self.workspace_dir}/distfiles")
            cmd_rewritten = cmd_rewritten.replace("/challenge/workspace", f"{self.workspace_dir}/workspace")
            cmd_rewritten = cmd_rewritten.replace("/challenge", self.workspace_dir)

            env = dict(os.environ)
            env["WORKSPACE"] = f"{self.workspace_dir}/workspace"
            env["DISTFILES"] = f"{self.workspace_dir}/distfiles"

            try:
                proc = await asyncio.create_subprocess_shell(
                    cmd_rewritten,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=f"{self.workspace_dir}/workspace",
                    env=env,
                    start_new_session=True,  # Process group for clean killing
                )
                self._active_processes.add(proc)

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=timeout_s,
                    )
                    return ExecResult(
                        exit_code=proc.returncode if proc.returncode is not None else 0,
                        stdout=stdout_bytes.decode("utf-8", errors="replace"),
                        stderr=stderr_bytes.decode("utf-8", errors="replace"),
                    )
                except TimeoutError:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    return ExecResult(
                        exit_code=-1,
                        stdout="",
                        stderr=f"Command timed out after {timeout_s}s",
                    )
                finally:
                    self._active_processes.discard(proc)
            except Exception as e:
                return ExecResult(exit_code=-1, stdout="", stderr=str(e))

    async def read_file(self, path: str) -> str | bytes:
        target = self._resolve_local_path(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path} (resolved {target})")

        data = target.read_bytes()
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data

    async def read_file_bytes(self, path: str) -> bytes:
        target = self._resolve_local_path(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path} (resolved {target})")
        return target.read_bytes()

    async def write_file(self, path: str, content: str | bytes) -> None:
        target = self._resolve_local_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding="utf-8")
        else:
            target.write_bytes(content)

    async def copy_from(self, container_path: str, host_path: str) -> None:
        data = await self.read_file_bytes(container_path)
        dest = Path(host_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    async def stop(self) -> None:
        for proc in list(self._active_processes):
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
        self._active_processes.clear()

        if self.workspace_dir:
            try:
                shutil.rmtree(self.workspace_dir, ignore_errors=True)
            except Exception:
                pass
            self.workspace_dir = ""
        logger.info("LocalSandbox stopped")


@dataclass
class DockerSandbox:
    """Isolated Docker container for a single solver agent with auto-fallback."""

    image: str
    challenge_dir: str
    memory_limit: str = "16g"
    workspace_dir: str = ""
    fallback_to_local: bool = True
    _container: Any = field(default=None, repr=False)
    _docker: Any = field(default=None, repr=False)
    _fallback_sandbox: LocalSandbox | None = field(default=None, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def container_id(self) -> str:
        if self._fallback_sandbox:
            return self._fallback_sandbox.container_id
        if not self._container:
            raise RuntimeError("Sandbox not started")
        return self._container.id

    def _parse_memory_limit(self) -> int:
        s = self.memory_limit.strip().lower()
        try:
            if s.endswith("g"):
                return int(s[:-1]) * 1024 * 1024 * 1024
            if s.endswith("m"):
                return int(s[:-1]) * 1024 * 1024
            return int(s)
        except (ValueError, IndexError):
            logger.warning("Invalid memory_limit %r, defaulting to 4GB", self.memory_limit)
            return 4 * 1024 * 1024 * 1024

    async def start(self) -> None:
        sem = _start_semaphore or asyncio.Semaphore(50)
        async with sem:
            try:
                self._docker = aiodocker.Docker()
                # Test connection
                await asyncio.wait_for(self._docker.version(), timeout=3.0)

                self.workspace_dir = tempfile.mkdtemp(prefix="ctf-workspace-")
                challenge_root = Path(self.challenge_dir).resolve()
                distfiles = str(challenge_root / "distfiles")
                meta_yml = str(challenge_root / "metadata.yml")

                binds: list[str] = [f"{self.workspace_dir}:/challenge/workspace:rw"]
                if Path(distfiles).exists():
                    binds.append(f"{distfiles}:/challenge/distfiles:ro")
                if Path(meta_yml).exists():
                    binds.append(f"{meta_yml}:/challenge/metadata.yml:ro")

                config = {
                    "Image": self.image,
                    "Cmd": ["sleep", "infinity"],
                    "WorkingDir": "/challenge",
                    "Tty": False,
                    "Labels": {CONTAINER_LABEL: "true"},
                    "HostConfig": {
                        "Binds": binds,
                        "ExtraHosts": ["host.docker.internal:host-gateway"],
                        "CapAdd": ["SYS_ADMIN", "SYS_PTRACE"],
                        "SecurityOpt": ["seccomp=unconfined"],
                        "Devices": [
                            {
                                "PathOnHost": "/dev/loop-control",
                                "PathInContainer": "/dev/loop-control",
                                "CgroupPermissions": "rwm",
                            }
                        ],
                        "Memory": self._parse_memory_limit(),
                        "NanoCpus": int(2 * 1e9),
                    },
                }

                self._container = await self._docker.containers.create(config)
                await self._container.start()
                await _track_start()

                info = await self._container.show()
                short_id = info["Id"][:12]
                logger.info("Docker sandbox started: %s", short_id)
            except Exception as e:
                if self.fallback_to_local:
                    logger.warning("Docker sandbox start failed (%s); falling back to LocalSandbox", e)
                    if self._docker:
                        try:
                            await self._docker.close()
                        except Exception:
                            pass
                        self._docker = None
                    self._fallback_sandbox = LocalSandbox(
                        image="local",
                        challenge_dir=self.challenge_dir,
                        memory_limit=self.memory_limit,
                    )
                    await self._fallback_sandbox.start()
                    self.workspace_dir = self._fallback_sandbox.workspace_dir
                    self._container = "local"
                else:
                    raise

    async def exec(self, command: str, timeout_s: int = 300) -> ExecResult:
        if self._fallback_sandbox:
            return await self._fallback_sandbox.exec(command, timeout_s)

        if not self._container:
            raise RuntimeError("Sandbox not started")

        async with self._lock:
            try:
                return await self._exec_inner(command, timeout_s)
            except aiodocker.exceptions.DockerError as e:
                return ExecResult(exit_code=-1, stdout="", stderr=f"Container error: {e}")

    async def _exec_inner(self, command: str, timeout_s: int) -> ExecResult:
        wrapped = f"timeout --signal=KILL --kill-after=5 {timeout_s} bash -c {shlex.quote(command)}"
        exec_instance = await self._container.exec(
            cmd=["bash", "-c", wrapped],
            stdout=True,
            stderr=True,
            tty=False,
        )

        stream = exec_instance.start(detach=False)
        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []

        async def _collect() -> None:
            while True:
                msg = await stream.read_out()
                if msg is None:
                    break
                if msg.stream == 1:
                    stdout_chunks.append(msg.data)
                else:
                    stderr_chunks.append(msg.data)

        try:
            await asyncio.wait_for(_collect(), timeout=timeout_s + 30)
        except TimeoutError:
            try:
                await stream.close()
            except Exception:
                pass
            return ExecResult(
                exit_code=-1,
                stdout=b"".join(stdout_chunks).decode("utf-8", errors="replace"),
                stderr="Command timed out",
            )

        inspect = await exec_instance.inspect()
        exit_code = inspect.get("ExitCode", 0)

        return ExecResult(
            exit_code=exit_code,
            stdout=b"".join(stdout_chunks).decode("utf-8", errors="replace"),
            stderr=b"".join(stderr_chunks).decode("utf-8", errors="replace"),
        )

    async def read_file(self, path: str) -> str | bytes:
        if self._fallback_sandbox:
            return await self._fallback_sandbox.read_file(path)

        if not self._container:
            raise RuntimeError("Sandbox not started")

        tar = await asyncio.wait_for(self._container.get_archive(path), timeout=30)
        with tar:
            for member in tar:
                if member.isfile():
                    f = tar.extractfile(member)
                    if f:
                        data = f.read()
                        try:
                            return data.decode("utf-8")
                        except UnicodeDecodeError:
                            return data
        raise FileNotFoundError(f"No file found at {path}")

    async def read_file_bytes(self, path: str) -> bytes:
        result = await self.read_file(path)
        if isinstance(result, str):
            return result.encode("utf-8")
        return result

    async def write_file(self, path: str, content: str | bytes) -> None:
        if self._fallback_sandbox:
            return await self._fallback_sandbox.write_file(path, content)

        if not self._container:
            raise RuntimeError("Sandbox not started")

        if isinstance(content, str):
            content = content.encode("utf-8")

        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            info = tarfile.TarInfo(name=Path(path).name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        buf.seek(0)

        await asyncio.wait_for(
            self._container.put_archive(str(Path(path).parent), buf.getvalue()),
            timeout=30,
        )

    async def copy_from(self, container_path: str, host_path: str) -> None:
        if self._fallback_sandbox:
            return await self._fallback_sandbox.copy_from(container_path, host_path)

        data = await self.read_file_bytes(container_path)
        Path(host_path).parent.mkdir(parents=True, exist_ok=True)
        Path(host_path).write_bytes(data)

    async def stop(self) -> None:
        if self._fallback_sandbox:
            await self._fallback_sandbox.stop()
            self._fallback_sandbox = None

        if self._container and self._container != "local":
            try:
                await self._container.delete(force=True)
            except Exception:
                pass
            self._container = None
            await _track_stop()

        if self._docker:
            try:
                await self._docker.close()
            except Exception:
                pass
            self._docker = None

        if self.workspace_dir:
            try:
                shutil.rmtree(self.workspace_dir, ignore_errors=True)
            except Exception:
                pass
            self.workspace_dir = ""
        logger.info("Docker sandbox stopped")


async def create_sandbox(
    image: str = "ctf-sandbox",
    challenge_dir: str = "",
    memory_limit: str = "16g",
    mode: str = "auto",
) -> SandboxProtocol:
    """Create a sandbox instance based on the desired execution mode."""
    if mode == "local":
        return LocalSandbox(image="local", challenge_dir=challenge_dir, memory_limit=memory_limit)

    if mode == "docker":
        return DockerSandbox(
            image=image,
            challenge_dir=challenge_dir,
            memory_limit=memory_limit,
            fallback_to_local=False,
        )

    # auto mode
    docker_ok = await is_docker_available()
    if docker_ok:
        return DockerSandbox(
            image=image,
            challenge_dir=challenge_dir,
            memory_limit=memory_limit,
            fallback_to_local=True,
        )

    logger.warning("Docker is not available; creating LocalSandbox")
    return LocalSandbox(image="local", challenge_dir=challenge_dir, memory_limit=memory_limit)
