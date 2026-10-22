from datetime import datetime, timedelta, timezone

from audit_site import Report, analyze_certificate, analyze_headers, exposed_path_finding

GOOD_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=()",
    "Server": "nginx",
}


def ids(findings):
    return {f.check_id for f in findings}


def test_hardened_site_has_no_findings():
    assert analyze_headers(GOOD_HEADERS, is_https=True) == []


def test_bare_site_reports_core_gaps():
    found = ids(analyze_headers({}, is_https=True))
    assert {"hsts-missing", "csp-missing", "clickjacking", "nosniff-missing"} <= found


def test_header_names_are_case_insensitive():
    lowered = {k.lower(): v for k, v in GOOD_HEADERS.items()}
    assert analyze_headers(lowered, is_https=True) == []


def test_hsts_not_required_on_http():
    assert "hsts-missing" not in ids(analyze_headers({}, is_https=False))


def test_short_hsts_is_flagged():
    headers = {**GOOD_HEADERS, "Strict-Transport-Security": "max-age=3600"}
    assert "hsts-short" in ids(analyze_headers(headers, is_https=True))


def test_version_disclosure():
    headers = {**GOOD_HEADERS, "Server": "Apache/2.4.41", "X-Powered-By": "PHP/7.4.3"}
    found = ids(analyze_headers(headers, is_https=True))
    assert {"disclosure-server", "disclosure-x-powered-by"} <= found


def test_insecure_cookie():
    headers = {**GOOD_HEADERS, "Set-Cookie": "session=abc; Path=/"}
    assert "cookie-session" in ids(analyze_headers(headers, is_https=True))


def test_x_frame_options_alone_protects_from_framing():
    headers = {**GOOD_HEADERS, "Content-Security-Policy": "default-src 'self'", "X-Frame-Options": "DENY"}
    assert "clickjacking" not in ids(analyze_headers(headers, is_https=True))


def _cert(days: int) -> dict:
    when = datetime.now(timezone.utc) + timedelta(days=days)
    return {"notAfter": when.strftime("%b %d %H:%M:%S %Y GMT")}


def test_certificate_states():
    assert analyze_certificate(_cert(90)) == []
    assert ids(analyze_certificate(_cert(5))) == {"tls-expiring"}
    assert ids(analyze_certificate(_cert(-3))) == {"tls-expired"}


def test_exposed_git_requires_real_content():
    assert exposed_path_finding("/.git/HEAD", 200, "ref: refs/heads/main") is not None
    assert exposed_path_finding("/.git/HEAD", 200, "<html>Not found</html>") is None
    assert exposed_path_finding("/.git/HEAD", 404, "") is None


def test_exposed_wp_users_requires_json_array():
    assert exposed_path_finding("/wp-json/wp/v2/users", 200, '[{"id":1}]') is not None
    assert exposed_path_finding("/wp-json/wp/v2/users", 200, '{"code":"rest_no_route"}') is None


def test_score_drops_with_severity():
    report = Report(url="https://x", checked_at="now", findings=analyze_headers({}, is_https=True))
    assert 0 <= report.score() < 100
    assert report.sorted_findings()[0].severity == "wysokie"
