from murdoku_lab.evaluation.analyse import failure_diagnostics


def test_failure_diagnostics_uses_persisted_protocol_signals():
    rows = [
        {
            "score": {"answer_correct": True, "placement_exact": False},
            "invalid_actions": 2,
            "python_calls": 1,
            "python_refusals": 1,
            "usage": {"completion_tokens": 100},
            "error": None,
            "transcript": [
                {"actions": [], "observations": ["No ACTION line found."]},
                {
                    "actions": ["python"],
                    "observations": ["REFUSED: open( is unavailable"],
                },
            ],
        },
        {
            "score": {"answer_correct": False, "placement_exact": False},
            "invalid_actions": 0,
            "python_calls": 1,
            "python_refusals": 0,
            "usage": {"completion_tokens": 300},
            "error": "RuntimeError: episode completion-token budget exhausted (400)",
            "transcript": [
                {
                    "actions": ["python"],
                    "observations": ["(no output — did you print anything?)"],
                },
            ],
        },
    ]

    report = failure_diagnostics(rows)
    values = {
        parts[0]: parts[1]
        for line in report.splitlines()[1:]
        if len(parts := line.split()) == 2
    }
    assert values == {
        "episodes_with_no_action_turn": "1",
        "no_action_turns": "1",
        "invalid_actions": "2",
        "python_calls": "2",
        "python_refusals": "1",
        "python_error_observations": "1",
        "python_no_output_observations": "1",
        "correct_verdict_without_exact_grid": "1",
        "completion_token_budget_exhausted": "1",
        "mean_completion_tokens": "200.0",
    }
