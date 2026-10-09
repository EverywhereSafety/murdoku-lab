"""Native puzzle actions and grading, shared by harness and isolated workers."""

from murdoku_lab.environment.state import apply_action
from murdoku_lab.environment.scoring import score_episode
from murdoku_lab.environment.rewards import terminal_reward


def apply_structured_action(pad, args, allow_check=True, reward_config=None):
    action = args.get("action")
    observations = []

    def execute(raw):
        observation, _ = apply_action(pad, raw)
        observations.append(observation)

    def atom(value, label):
        if not isinstance(value, str) or "\n" in value or "\r" in value:
            raise ValueError(label + " must be text without line breaks")
        return value

    if action in ("board", "check"):
        if action == "check" and not allow_check:
            observations.append("check is disabled")
        else:
            execute(action)
    elif action in ("place", "unplace", "mark", "unmark"):
        person = atom(args.get("person"), "person")
        cell = atom(args.get("cell", ""), "cell")
        execute(action + " " + person + " " + cell)
    elif action == "submit":
        placements = args.get("placements", {})
        if not isinstance(placements, dict):
            raise ValueError("placements must map names to cells")
        for person, cell in placements.items():
            execute("place " + atom(person, "person") + " " + atom(cell, "cell"))
        answer = atom(args.get("murderer", args.get("answer", "")), "answer")
        score = score_episode(pad.case, pad.theme, pad, answer)
        return {
            "done": True,
            "observations": observations + ["Submitted."],
            "reward": terminal_reward(score, len(pad.case.characters), reward_config),
            "final_state_variable": float(score["solved"]),
            "score": score,
        }
    else:
        raise ValueError(
            "unknown action; use board, place, unplace, mark, unmark, check or submit"
        )
    return {"done": False, "observations": observations}
