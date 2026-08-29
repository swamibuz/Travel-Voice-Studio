from app.auth import hash_password, verify_password


def test_hash_password_round_trip() -> None:
    stored = hash_password("admin123", "fixedsalt")
    assert stored.startswith("pbkdf2_sha256$")
    assert verify_password("admin123", stored)
    assert not verify_password("wrong", stored)


def test_verify_legacy_plain_password() -> None:
    assert verify_password("admin123", "admin123")
