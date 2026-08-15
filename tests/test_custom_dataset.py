import json

from performance_lab.datasets import (
    DatasetImportConfig,
    FieldMapping,
    SamplingSpec,
    inspect_dataset_source,
    load_dataset_import_config,
    materialize_dataset_import,
)


def test_source_inspection_exposes_shape_without_guessing_mapping(tmp_path) -> None:
    source = tmp_path / "dataset.jsonl"
    source.write_text(
        "\n".join(
            (
                json.dumps({"uid": "1", "question": "A", "answer": "x", "split": "test"}),
                json.dumps({"uid": "2", "question": "B", "answer": "y", "split": "train"}),
            )
        ),
        encoding="utf-8",
    )

    inspection = inspect_dataset_source(source, preview_limit=1)

    assert inspection.format == "jsonl"
    assert inspection.row_count == 2
    assert inspection.fields == ("answer", "question", "split", "uid")
    assert tuple(inspection.preview[0]) == ("uid", "question", "answer", "split")


def test_versioned_mapping_config_can_be_reused_for_materialization(tmp_path) -> None:
    source = tmp_path / "dataset.csv"
    source.write_text(
        "uid,prompt,target,split\n1,first,yes,test\n2,second,no,test\n3,third,yes,train\n",
        encoding="utf-8",
    )
    config_path = tmp_path / "mapping.json"
    config_path.write_text(
        DatasetImportConfig(
            dataset_id="custom-demo",
            dataset_version="v1",
            mapping=FieldMapping(
                id_field="uid",
                input_field="prompt",
                expected_field="target",
                split_field="split",
            ),
            sampling=SamplingSpec(seed=11, sample_limit=1),
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )

    config = load_dataset_import_config(config_path)
    first = materialize_dataset_import(source, config)
    second = materialize_dataset_import(source, config)

    assert first == second
    assert first.snapshot.dataset_id == "custom-demo"
    assert first.snapshot.sample_count == 1
    assert first.snapshot.content_sha256 == second.snapshot.content_sha256
