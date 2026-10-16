from backend.tools.ctf_helpers import do_quick_decode, extract_flag_candidates


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
