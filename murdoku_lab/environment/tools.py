"""Direct scientific-tool harness. Only public messages go to the model."""

from murdoku_lab.core.instance import Case
from murdoku_lab.core.theme import Theme, canonical_theme
from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.environment.scoring import score_episode
from murdoku_lab.environment.python import run_python
from murdoku_lab.environment.rewards import terminal_reward
from long_horizon_rl.memory import NotesStore, operate_notes

from murdoku_lab.environment.actions import apply_structured_action


class MurdokuToolEnvironment:
    def __init__(self, record, memory_path=None):
        self.record = record
        if record.get("murdoku_observation", "text") not in ("text", "vision"):
            raise ValueError("murdoku_observation must be text or vision")
        from long_horizon_rl.python_workspace import PythonWorkspace

        self.workspace = PythonWorkspace() if record.get("python_workspace") else None
        self.notes = NotesStore(memory_path) if memory_path is not None else None
        self.memory = self.notes.memory if self.notes else {}
        case = Case.from_json(record["murdoku_case"])
        theme = (
            Theme.from_json(record["murdoku_theme"])
            if record.get("murdoku_theme")
            else canonical_theme(case)
        )
        theme.validate(case)
        self.pad = Scratchpad(case, theme)
        self.done = False
        self.board_revision = 0
        self.presentation_notes = []

    def render_png(self, *, scope="board", style="art"):
        from murdoku_lab.visual.projection import public_observation
        from murdoku_lab.visual.art import board_svg, scene_svg, observation_svg
        from murdoku_lab.visual.raster import png_from_svg

        renderers = {"board": board_svg, "scene": scene_svg, "full": observation_svg}
        if scope not in renderers:
            raise ValueError("unknown image scope")
        observation = public_observation(self.pad, revision=self.board_revision)
        return png_from_svg(renderers[scope](observation, style=style))

    async def finalize(self, reason):
        if reason not in (
            "turn_limit",
            "generation_limit",
            "context_limit",
            "context_overflow",
            "immutable_context_overflow",
        ):
            raise ValueError("invalid normal stopping reason")
        score = score_episode(self.pad.case, self.pad.theme, self.pad, None)
        self.done = True
        return {
            "done": True,
            "reward": terminal_reward(
                score, len(self.pad.case.characters), self.record.get("murdoku_reward")
            ),
            "score": score,
        }

    async def start(self):
        return self

    async def close(self):
        if self.workspace is not None:
            self.workspace.close(getattr(self, "workspace_export_path", None))

    async def step(self, call):
        if self.done:
            raise ValueError("episode already ended")
        if call["tool"] == "memory":
            return (
                self.notes.operate(call["arguments"])
                if self.notes
                else operate_notes(self.memory, call["arguments"])
            )
        if call["tool"] == "workspace":
            if self.workspace is None:
                raise ValueError("workspace is not enabled")
            return self.workspace.operate(call["arguments"])
        if call["tool"] == "run_python":
            args = call["arguments"]
            budget = (
                args.get("timeout", self.record.get("python_timeout_seconds", 120))
                if self.workspace
                else 30
            )
            return await run_python(
                args.get("code"),
                timeout=budget,
                workspace=self.workspace,
                path=args.get("path"),
            )
        if (
            call["tool"] == "case_note"
            and self.record.get("murdoku_observation") == "vision"
        ):
            from murdoku_lab.environment.validation import validate_note

            self.presentation_notes.append(validate_note(call["arguments"], self.pad))
            return {
                "done": False,
                "observations": ["Public presentation note recorded."],
            }
        if call["tool"] != "murdoku":
            raise ValueError("unknown tool")
        if (
            self.record.get("murdoku_observation") == "vision"
            and call["arguments"].get("action") == "board"
        ):
            if set(call["arguments"]) != {"action"}:
                raise ValueError("board accepts only action")
            return {
                "done": False,
                "observations": ["Current board image requested."],
                "image_request": {
                    "scope": "board",
                    "format": "png",
                    "revision": self.board_revision,
                },
            }
        result = apply_structured_action(
            self.pad,
            call["arguments"],
            self.record.get("allow_check", True),
            self.record.get("murdoku_reward"),
        )
        self.done = result["done"]
        self.board_revision += 1
        return result
