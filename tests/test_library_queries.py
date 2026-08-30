from performance_lab.application import UIQueryService
from performance_lab.datasets import MaterializedDataset, build_general_starter_suite
from performance_lab.domain import DatasetSnapshot
from performance_lab.storage import SQLiteRunStore


def _queries(tmp_path, *, inspectable: bool = True) -> tuple[UIQueryService, object]:
    bundle = build_general_starter_suite()
    queries = UIQueryService(
        SQLiteRunStore(tmp_path / "runs.sqlite3"),
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        inspectable_datasets=tuple(bundle.datasets.values()) if inspectable else (),
        evaluators=tuple(bundle.evaluators.values()),
    )
    return queries, bundle


def test_benchmark_detail_projects_exact_definition_cases_and_evaluator_rules(tmp_path) -> None:
    queries, bundle = _queries(tmp_path)

    detail = queries.get_benchmark(bundle.suite.suite_id, bundle.suite.suite_version)

    assert detail.summary.suite_id == "general-diagnostic-starter"
    assert detail.summary.suite_version == bundle.suite.suite_version
    assert detail.summary.task_count == 7
    assert detail.definition_issues == ()
    assert len(detail.cases) == 23

    first = next(case for case in detail.cases if case.case_id == "instruction_following:if-1")
    assert first.input == "Reply with exactly: BLUE"
    assert first.expected == "BLUE"
    assert first.metric_names == ("normalized_exact_match",)

    numeric = next(task for task in detail.tasks if task.task_id == "basic_math")
    assert numeric.case_count == 4
    assert numeric.case_content_available is True
    assert numeric.evaluator.deterministic is True
    assert numeric.evaluator.configuration["absolute_tolerance"] == 1e-9
    assert "weight" not in numeric.evaluator.model_fields

    structured_cases = [
        case for case in detail.cases if case.dataset_id == "starter-structured"
    ]
    assert len(structured_cases) == 6
    assert {case.task_id for case in structured_cases} == {
        "structured_json_adherence",
        "structured_json_fields",
    }


def test_benchmark_detail_does_not_expose_case_content_without_explicit_materialization(
    tmp_path,
) -> None:
    queries, bundle = _queries(tmp_path, inspectable=False)

    detail = queries.get_benchmark(bundle.suite.suite_id, bundle.suite.suite_version)

    assert detail.cases == ()
    assert all(task.case_content_available is False for task in detail.tasks)
    assert sum(task.case_count or 0 for task in detail.tasks) == 23
    assert detail.definition_issues == ()


def test_mismatched_materialized_dataset_is_not_exposed_as_benchmark_content(tmp_path) -> None:
    bundle = build_general_starter_suite()
    original = bundle.datasets["starter-instruction"]
    mismatched_snapshot = DatasetSnapshot(
        **{
            **original.snapshot.model_dump(mode="python"),
            "content_sha256": "f" * 64,
        }
    )
    mismatched = MaterializedDataset(snapshot=mismatched_snapshot, records=original.records)
    queries = UIQueryService(
        SQLiteRunStore(tmp_path / "runs.sqlite3"),
        suites=(bundle.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in bundle.datasets.values()),
        inspectable_datasets=(mismatched,),
        evaluators=tuple(bundle.evaluators.values()),
    )

    detail = queries.get_benchmark(bundle.suite.suite_id, bundle.suite.suite_version)
    instruction = next(task for task in detail.tasks if task.task_id == "instruction_following")

    assert instruction.case_content_available is False
    assert not any(case.task_id == "instruction_following" for case in detail.cases)
    assert detail.definition_issues == (
        "Inspectable dataset does not match registered snapshot: starter-instruction",
    )


def test_benchmark_lookup_requires_exact_suite_version(tmp_path) -> None:
    queries, bundle = _queries(tmp_path)

    try:
        queries.get_benchmark(bundle.suite.suite_id, "missing")
    except LookupError as exc:
        assert "benchmark definition not found" in str(exc)
    else:
        raise AssertionError("missing benchmark version must raise LookupError")
