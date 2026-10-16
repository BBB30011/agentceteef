import pytest

from backend.sandbox import LocalSandbox, is_docker_available


@pytest.mark.asyncio
async def test_local_sandbox_lifecycle():
    sandbox = LocalSandbox(image="local")
    await sandbox.start()
    assert sandbox.workspace_dir != ""

    # Test execution
    res = await sandbox.exec("echo 'CTF_SANDBOX_OK'")
    assert res.exit_code == 0
    assert "CTF_SANDBOX_OK" in res.stdout

    # Test file write and read
    await sandbox.write_file("test.txt", "flag{sample_flag_123}")
    content = await sandbox.read_file("test.txt")
    assert content == "flag{sample_flag_123}"

    # Test file read with container path convention
    content2 = await sandbox.read_file("/challenge/workspace/test.txt")
    assert content2 == "flag{sample_flag_123}"


    # Test timeout
    res_timeout = await sandbox.exec("sleep 10", timeout_s=1)
    assert res_timeout.exit_code == -1
    assert "timed out" in res_timeout.stderr

    await sandbox.stop()


@pytest.mark.asyncio
async def test_docker_available_check():
    # Should complete without throwing an unhandled exception
    res = await is_docker_available()
    assert isinstance(res, bool)
