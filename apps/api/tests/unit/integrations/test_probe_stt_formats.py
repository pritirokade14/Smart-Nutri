"""scripts/probe_stt_formats.py never spends credits unless told to."""

import httpx

from scripts import probe_stt_formats


def _no_network(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("the probe must not touch the network without --yes-spend")

    monkeypatch.setattr(httpx.Client, "post", boom)


def test_dry_run_refuses_to_spend(monkeypatch, capsys):
    _no_network(monkeypatch)
    assert probe_stt_formats.main([]) == 2
    out = capsys.readouterr().out
    assert "--yes-spend" in out and "5 paid STT calls" in out


def test_refuses_in_ci_even_with_yes_spend(monkeypatch, capsys):
    _no_network(monkeypatch)
    monkeypatch.setenv("CI", "true")
    assert probe_stt_formats.main(["--yes-spend"]) == 2
    assert "CI" in capsys.readouterr().out


def test_probes_every_accepted_client_format():
    mimes = {mime for _, mime in probe_stt_formats.FORMATS.values()}
    assert mimes == {"audio/wav", "audio/mp4", "audio/webm", "audio/ogg", "audio/mpeg"}
