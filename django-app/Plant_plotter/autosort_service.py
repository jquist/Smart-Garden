from .phantom_box_optimizer import optimise_payload_boxes
from .solvers.simple_solver import run_autosort_simple
from .solvers.backtracking_solver import run_autosort_backtracking
from .solvers.constraint_solver import run_autosort_constraint


def _has_unplaced_plants(result):
    if not isinstance(result, dict):
        return False

    for key in ("unplaced", "unplaced_plants", "not_placed", "failed_plants"):
        value = result.get(key)
        if isinstance(value, list) and len(value) > 0:
            return True

    return False


def _run_selected_solver(payload):
    algorithm = payload.get("algorithm", "quick")

    if algorithm in ("quick", "quick_fill"):
        quick_payload = dict(payload)
        quick_payload["fill"] = algorithm == "quick_fill" or bool(payload.get("fill", False))
        return run_autosort_simple(quick_payload)

    if algorithm in ("backtracking_k", "backtracking_minmax"):
        backtracking_payload = dict(payload)
        backtracking_payload["k"] = int(payload.get("k", 6 if algorithm == "backtracking_minmax" else 3))
        backtracking_payload["fill"] = algorithm == "backtracking_minmax" or bool(payload.get("fill", False))
        return run_autosort_backtracking(backtracking_payload)

    if algorithm in ("constraint", "constraint_fill"):
        constraint_payload = dict(payload)
        constraint_payload["fill"] = algorithm == "constraint_fill" or bool(payload.get("fill", False))
        return run_autosort_constraint(constraint_payload)

    raise ValueError("Unknown algorithm selected.")


def run_autosort(payload):
    """Run autosort with a safe phantom-box pre-pass.

    The phantom-box optimiser only changes the boxes sent into the selected
    solver. If the optimised attempt errors or leaves plants unplaced, the same
    solver is retried with the original full-size boxes.
    """
    original_payload = dict(payload)
    optimised_payload = optimise_payload_boxes(original_payload)

    phantom_used = optimised_payload.get("boxes") != original_payload.get("boxes")

    if not phantom_used:
        return _run_selected_solver(original_payload)

    try:
        result = _run_selected_solver(optimised_payload)
        if _has_unplaced_plants(result):
            fallback_result = _run_selected_solver(original_payload)
            if isinstance(fallback_result, dict):
                fallback_result["phantom_box_info"] = {
                    **optimised_payload.get("phantom_box_info", {}),
                    "fallback_used": True,
                    "fallback_reason": "phantom_result_had_unplaced_plants",
                }
            return fallback_result

        if isinstance(result, dict):
            result["phantom_box_info"] = {
                **optimised_payload.get("phantom_box_info", {}),
                "fallback_used": False,
            }
        return result

    except Exception:
        fallback_result = _run_selected_solver(original_payload)
        if isinstance(fallback_result, dict):
            fallback_result["phantom_box_info"] = {
                **optimised_payload.get("phantom_box_info", {}),
                "fallback_used": True,
                "fallback_reason": "phantom_solver_error",
            }
        return fallback_result
