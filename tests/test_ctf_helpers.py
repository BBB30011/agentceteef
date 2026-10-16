from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.tools.ctf_helpers import (
    do_auto_decode,
    do_entropy,
    do_extract_archive,
    do_identify_hash,
    do_jwt_decode,
    do_quick_decode,
    do_rot_bruteforce,
    do_single_byte_xor,
    extract_flag_candidates,
)
from backend.tools.self_healing import diagnose_execution_error


def test_extract_flag_candidates():
    sample = """
    Log output:
    Checking user credentials...
    Nothing here: CTF{placeholder}
    Real flag found: CTF{super_secret_flag_2026}
    Another one: picoCTF{hash_value_here}
    """
    flags = extract_flag_candidates(sample)
    assert "CTF{super_secret_flag_2026}" in flags
    assert "picoCTF{hash_value_here}" in flags
    assert "CTF{placeholder}" not in flags


def test_quick_decode():
    assert do_quick_decode("aGVsbG8gd29ybGQ=", "base64") == "hello world"
    assert do_quick_decode("68656c6c6f", "hex") == "hello"
    assert do_quick_decode("uryyb", "rot13") == "hello"
    assert do_quick_decode("hello%20world", "url") == "hello world"


def test_auto_decode_single_layer():
    # flag{single_layer_b64} encoded in base64: ZmxhZ3tzaW5nbGVfbGF5ZXJfYjY0fQ==
    res = do_auto_decode("ZmxhZ3tzaW5nbGVfbGF5ZXJfYjY0fQ==")
    assert "flag{single_layer_b64}" in res
    assert "FLAG(S) REVEALED" in res


def test_auto_decode_cascade():
    # flag{cascade_magic} -> rot13: synt{pnfpnqr_zntvp} -> base64: c3ludHtwbmZwbnFyX3pudHZwfQ==
    res = do_auto_decode("c3ludHtwbmZwbnFyX3pudHZwfQ==")
    assert "flag{cascade_magic}" in res
    assert "base64 -> rot13" in res


def test_single_byte_xor():
    # 'flag{xor_cracked}' XOR 0x42
    flag_bytes = b"flag{xor_cracked}"
    xored = bytes([b ^ 0x42 for b in flag_bytes])
    res = do_single_byte_xor(xored.hex())
    assert "flag{xor_cracked}" in res
    assert "Key 0x42" in res


def test_identify_hash():
    md5_hash = "5d41402abc4b2a76b9719d911017c592"
    sha256_hash = "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
    bcrypt_hash = "$2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW"

    assert "MD5" in do_identify_hash(md5_hash)
    assert "SHA-256" in do_identify_hash(sha256_hash)
    assert "bcrypt" in do_identify_hash(bcrypt_hash)


def test_entropy():
    # Plain text should have lower entropy than uniform random bytes
    low_ent = do_entropy("AAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBBBBBBB")
    assert low_ent < 2.0
    import os
    high_ent = do_entropy(os.urandom(1000))
    assert high_ent > 7.5


def test_rot_bruteforce():
    # ROT-13 of "flag{rot_caesar_solved}" is "synt{ebg_pnrfne_fbyirq}"
    cipher = "synt{ebg_pnrfne_fbyirq}"
    res = do_rot_bruteforce(cipher)
    assert "flag{rot_caesar_solved}" in res
    assert "FLAG DETECTED at ROT-13" in res


def test_jwt_decode():
    # Header: {"alg": "none", "typ": "JWT"} -> eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0
    # Payload: {"admin": false, "user": "guest", "flag": "flag{jwt_token_claims_revealed}"}
    # -> eyJhZG1pbiI6IGZhbHNlLCAidXNlciI6ICJndWVzdCIsICJmbGFnIjogImZsYWd7and0X3Rva2VuX2NsYWltc19yZXZlYWxlZH0ifQ
    token = "eyJhbGciOiAibm9uZSIsICJ0eXAiOiAiSldUIn0.eyJhZG1pbiI6IGZhbHNlLCAidXNlciI6ICJndWVzdCIsICJmbGFnIjogImZsYWd7and0X3Rva2VuX2NsYWltc19yZXZlYWxlZH0ifQ."
    res = do_jwt_decode(token)
    assert "flag{jwt_token_claims_revealed}" in res
    assert "CRITICAL: Token algorithm is set to 'none'" in res
    assert "'admin' claim is false" in res


@pytest.mark.asyncio
async def test_extract_archive_mock():
    sandbox = MagicMock()
    exec_res1 = MagicMock(stdout="-rw-r--r-- 1 kali kali 120 secret.txt\n", stderr="", exit_code=0)
    exec_res2 = MagicMock(stdout="flag{extracted_from_tarball_2026}\n", stderr="", exit_code=0)
    sandbox.exec = AsyncMock(side_effect=[exec_res1, exec_res2])

    res = await do_extract_archive(sandbox, "/challenge/distfiles/archive.tar.gz", "/challenge/workspace/out")
    assert "Archive Extraction" in res
    assert "flag{extracted_from_tarball_2026}" in res


def test_self_healing_diagnostics():
    # Module missing
    res1 = diagnose_execution_error("ModuleNotFoundError: No module named 'pwntools'")
    assert res1 is not None and "pip install pwntools" in res1

    # Segfault
    res2 = diagnose_execution_error("Segmentation fault (core dumped)", exit_code=139)
    assert res2 is not None and "Segmentation Fault (SIGSEGV / code 139)" in res2
    assert "gdb" in res2

    # Stack smashing
    res3 = diagnose_execution_error("*** stack smashing detected ***: terminated")
    assert res3 is not None and "Stack Canary" in res3

    # Connection refused
    res4 = diagnose_execution_error("Errno 111 Connection refused")
    assert res4 is not None and "Connection Refused" in res4

    # Permission denied
    res5 = diagnose_execution_error("bash: ./exploit.sh: Permission denied", exit_code=126)
    assert res5 is not None and "chmod +x" in res5

    # Command not found
    res6 = diagnose_execution_error("bash: r2: command not found", exit_code=127, command="r2 ./bin")
    assert res6 is not None and "r2" in res6

    # Unicode error
    res7 = diagnose_execution_error("UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfe")
    assert res7 is not None and "'rb'" in res7

