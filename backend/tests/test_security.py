from app.security import RateLimiter, je_zabranjen_host, provjeri_admin, provjeri_url


def test_ssrf_blokira_localhost_i_privatne():
    assert je_zabranjen_host("localhost")
    for u in ("http://localhost:8080/x", "http://127.0.0.1/", "http://169.254.169.254/latest",
              "http://10.0.0.1/", "ftp://x.test/"):
        try:
            provjeri_url(u)
            assert False, u
        except ValueError:
            pass


def test_rate_limiter():
    rl = RateLimiter(2)
    assert rl.dozvoli("k") and rl.dozvoli("k") and not rl.dozvoli("k")


def test_admin_token_constant_time():
    assert provjeri_admin("abc", "abc") and not provjeri_admin("abc", "abd") and not provjeri_admin("", "abd")


def test_konektor_greska_ne_rusi_sken(monkeypatch):
    import app.connectors as c
    monkeypatch.setattr(c, "_fetch", lambda *a, **k: (_ for _ in ()).throw(Exception("pad")))
    o, nap = c.GreenhouseKonektor().skeniraj()
    assert o == [] and nap is not None
