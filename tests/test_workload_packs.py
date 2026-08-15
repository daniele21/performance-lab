import pytest

from performance_lab.datasets import (
    STRUCTURED_DOCUMENT_EXTRACTION,
    available_workload_packs,
    build_workload_pack,
)


def test_workload_registry_exposes_versioned_pack_without_engine_coupling() -> None:
    definitions = available_workload_packs()

    assert definitions == (STRUCTURED_DOCUMENT_EXTRACTION,)
    assert definitions[0].pack_id == "structured-document-extraction"
    assert definitions[0].task_family == "structured_extraction"


def test_structured_document_pack_is_deterministic_and_uses_objective_evaluators() -> None:
    first = build_workload_pack("structured-document-extraction")
    second = build_workload_pack(
        "structured-document-extraction",
        version=STRUCTURED_DOCUMENT_EXTRACTION.version,
    )

    assert first.definition == second.definition
    assert first.suite == second.suite
    assert first.datasets == second.datasets
    assert first.suite.generation.response_format == "json_object"
    assert first.suite.generation.temperature == 0.0
    assert tuple(task.task_id for task in first.suite.tasks) == (
        "schema_adherence",
        "field_correctness",
    )
    dataset = first.datasets["workload-structured-document-extraction"]
    assert dataset.snapshot.sample_count == 6
    assert dataset.snapshot.content_sha256 == second.datasets[
        "workload-structured-document-extraction"
    ].snapshot.content_sha256
    assert all("Document:" in record.input for record in dataset.records)


def test_unknown_workload_or_version_is_rejected_explicitly() -> None:
    with pytest.raises(KeyError):
        build_workload_pack("unknown-pack")
    with pytest.raises(KeyError):
        build_workload_pack("structured-document-extraction", version="old")
