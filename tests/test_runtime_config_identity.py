from performance_lab.domain import RuntimeIdentity


def test_runtime_identity_preserves_serving_config_digest() -> None:
    identity = RuntimeIdentity(
        name="llama_cpp",
        version="0.3.15",
        config_digest="a" * 64,
    )

    assert identity.config_digest == "a" * 64
