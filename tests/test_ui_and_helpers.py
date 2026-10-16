import tempfile
from pathlib import Path

from backend.state import StateManager
from backend.tools.ctf_helpers import do_auto_decode, do_entropy
from backend.ui.dashboard import format_category_badge
from backend.ui.exporter import export_report_to_file, generate_html_report


def test_do_auto_decode():
    # Base64 with flag
    b64_input = "ZmxhZ3thdXRvX2RlY29kZV9zdWNjZXNzXzEzMzd9"
    res = do_auto_decode(b64_input)
    assert "flag{auto_decode_success_1337}" in res
    assert "FLAG(S) REVEALED" in res

    # Hex with flag
    hex_input = "666c61677b6865785f77696e5f3939397d"
    res_hex = do_auto_decode(hex_input)
    assert "flag{hex_win_999}" in res_hex

    # Rot13 with flag
    # "flag{rot13_works}" in rot13 is "synt{ebg13_jbexf}"
    res_rot = do_auto_decode("synt{ebg13_jbexf}")
    assert "flag{rot13_works}" in res_rot


def test_do_entropy():
    # Low entropy (plain text repeated)
    low_ent = do_entropy("AAAAAAAAAA")
    assert low_ent == 0.0

    # Normal text
    text_ent = do_entropy("The quick brown fox jumps over the lazy dog")
    assert 3.0 < text_ent < 5.0

    # High entropy (random bytes)
    high_ent = do_entropy(bytes(range(256)))
    assert high_ent == 8.0


def test_format_category_badge():
    badge_pwn = format_category_badge("pwn")
    assert "PWN" in badge_pwn
    badge_rev = format_category_badge("rev")
    assert "REV" in badge_rev


def test_html_report_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_state.sqlite3")
        state = StateManager(db_path)
        state.record_discovered("sample_pwn", "pwn", 250)
        state.record_submission("sample_pwn", "flag{sample_flag}", "correct", "ACCEPTED", "agy/default")
        state.mark_solved("sample_pwn", "flag{sample_flag}", "agy/default", solve_time=15.4)

        html = generate_html_report(state)
        assert "<!DOCTYPE html>" in html
        assert "sample_pwn" in html
        assert "flag{sample_flag}" in html
        assert "agy/default" in html

        out_file = str(Path(tmpdir) / "report.html")
        export_report_to_file(state, out_file)
        assert Path(out_file).exists()
        assert Path(out_file).read_text().startswith("<!DOCTYPE html>")
