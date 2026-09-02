from performance_lab.datasets import STARTER_SUITE_VERSION, build_general_starter_suite


def test_starter_suite_is_versioned_and_covers_core_categories() -> None:
    bundle = build_general_starter_suite()
    assert bundle.suite.suite_version == STARTER_SUITE_VERSION
    assert {task.task_id for task in bundle.suite.tasks} == {
        "instruction_following",
        "factual_qa",
        "reasoning",
        "basic_math",
        "classification",
        "structured_json_adherence",
        "structured_json_fields",
    }


def test_starter_suite_snapshots_are_deterministic() -> None:
    first = build_general_starter_suite()
    second = build_general_starter_suite()
    assert first.suite == second.suite
    assert {
        dataset_id: dataset.snapshot.content_sha256
        for dataset_id, dataset in first.datasets.items()
    } == {
        dataset_id: dataset.snapshot.content_sha256
        for dataset_id, dataset in second.datasets.items()
    }
    assert all(
        dataset.snapshot.source == "builtin:performance-lab-authored"
        for dataset in first.datasets.values()
    )


def test_starter_suite_is_small_enough_for_local_diagnostics() -> None:
    bundle = build_general_starter_suite()
    total_records = sum(len(dataset.records) for dataset in bundle.datasets.values())
    assert total_records == 20
    assert total_records <= 25


def test_all_task_evaluators_are_supplied() -> None:
    bundle = build_general_starter_suite()
    for task in bundle.suite.tasks:
        evaluator = bundle.evaluators[task.evaluator.evaluator_id]
        assert evaluator.version == task.evaluator.version
