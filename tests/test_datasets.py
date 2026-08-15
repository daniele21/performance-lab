import json

import pytest

from performance_lab.datasets import (
    DatasetLoadError,
    FieldMapping,
    LocalDatasetLoader,
    SamplingSpec,
    materialize_local_dataset,
)


def test_jsonl_split_and_sampling_are_deterministic(tmp_path) -> None:
    source = tmp_path / "dataset.jsonl"
    rows = [
        {"id": str(index), "prompt": f"q{index}", "answer": f"a{index}", "split": "test"}
        for index in range(8)
    ]
    rows.append({"id": "train", "prompt": "qt", "answer": "at", "split": "train"})
    source.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    kwargs = dict(
        dataset_id="demo",
        dataset_version="1",
        split="test",
        mapping=FieldMapping(
            id_field="id",
            input_field="prompt",
            expected_field="answer",
            split_field="split",
        ),
        sampling=SamplingSpec(seed=42, sample_limit=3),
    )
    first = materialize_local_dataset(source, **kwargs)
    second = materialize_local_dataset(source, **kwargs)

    assert [record.sample_id for record in first.records] == [
        record.sample_id for record in second.records
    ]
    assert first.snapshot.content_sha256 == second.snapshot.content_sha256
    assert first.snapshot.sample_count == 3
    assert "limit=3" in first.snapshot.selection_policy
    assert all(record.metadata["split"] == "test" for record in first.records)


def test_digest_changes_when_selected_content_changes(tmp_path) -> None:
    source = tmp_path / "dataset.jsonl"
    source.write_text(
        json.dumps({"id": "1", "prompt": "question", "answer": "a"}),
        encoding="utf-8",
    )
    mapping = FieldMapping(id_field="id", input_field="prompt", expected_field="answer")
    first = materialize_local_dataset(
        source,
        dataset_id="demo",
        dataset_version="1",
        split="test",
        mapping=mapping,
    )

    source.write_text(
        json.dumps({"id": "1", "prompt": "question", "answer": "b"}),
        encoding="utf-8",
    )
    second = materialize_local_dataset(
        source,
        dataset_id="demo",
        dataset_version="1",
        split="test",
        mapping=mapping,
    )

    assert first.snapshot.content_sha256 != second.snapshot.content_sha256


def test_csv_loader_requires_explicit_mapping(tmp_path) -> None:
    source = tmp_path / "dataset.csv"
    source.write_text("sample,prompt,label\n1,hello,yes\n", encoding="utf-8")
    materialized = materialize_local_dataset(
        source,
        dataset_id="csv-demo",
        dataset_version="1",
        split="all",
        mapping=FieldMapping(
            id_field="sample",
            input_field="prompt",
            expected_field="label",
        ),
    )
    assert materialized.records[0].input == "hello"
    assert materialized.records[0].expected == "yes"


def test_loader_rejects_unsupported_format(tmp_path) -> None:
    source = tmp_path / "dataset.txt"
    source.write_text("x", encoding="utf-8")
    with pytest.raises(DatasetLoadError):
        LocalDatasetLoader().load(source)
