from backend.tools.ctf_helpers import (
    do_auto_decode,
    do_entropy,
    do_identify_hash,
    do_quick_decode,
    do_single_byte_xor,
    extract_flag_candidates,
)


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
