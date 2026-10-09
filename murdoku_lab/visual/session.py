"""Stateful player session using shared puzzle actions and grading."""

from copy import deepcopy
import threading
import uuid

from murdoku_lab.environment.state import Scratchpad
from murdoku_lab.environment.actions import apply_structured_action
from murdoku_lab.visual.projection import public_observation


from murdoku_lab.environment.validation import (
    SessionError,
    validate_note,
    validate_tool_action,
)


class StaleRevision(SessionError):
    pass


class VisualSession:
    def __init__(self, entry, *, allow_check=True, reward_config=None):
        self.entry = entry
        self.id = uuid.uuid4().hex
        self.pad = Scratchpad(entry.case, entry.theme)
        self.allow_check = allow_check
        self.reward_config = reward_config
        self.revision = 0
        self.done = False
        self.terminal = None
        self.reviewed = set()
        self.notebook = ""
        self.pending_note = None
        self.undo_stack = []
        self.redo_stack = []
        self.events = []
        self.lock = threading.RLock()
        self.frames = [self.observe()]

    def _snapshot(self):
        return deepcopy((self.pad.placed, self.pad.marks, self.reviewed, self.notebook))

    def _restore(self, snap):
        self.pad.placed, self.pad.marks, self.reviewed, self.notebook = deepcopy(snap)

    def observe(self):
        return public_observation(
            self.pad,
            session_id=self.id,
            case_id=self.entry.slug,
            revision=self.revision,
            reviewed=self.reviewed,
            notebook=self.notebook,
            done=self.done,
            terminal=self.terminal,
            can_undo=bool(self.undo_stack),
            can_redo=bool(self.redo_stack),
            setting=self.entry.setting,
            eyebrow=self.entry.eyebrow,
            last_event=self.events[-1] if self.events else None,
        )

    def act(self, args, *, note=None, expected_revision=None, source="tool"):
        with self.lock:
            if expected_revision is not None and (
                type(expected_revision) is not int or expected_revision != self.revision
            ):
                raise StaleRevision(
                    "The session changed. Fetch the current observation and retry."
                )
            if self.done:
                raise SessionError("Episode ended. Start a new session to try again.")
            if len(self.events) >= 1000:
                raise SessionError(
                    "This local demo session has reached its 1000-event limit."
                )
            note = validate_note(note, self.pad)
            if not isinstance(args, dict):
                raise SessionError("action must be an object")
            action = args.get("action")
            if note is None and action != "present":
                note = deepcopy(self.pending_note)
            previous = self._snapshot()
            if action in ("undo", "redo"):
                if set(args) != {"action"}:
                    raise SessionError("undo/redo only accepts action")
                src, dst = (
                    (self.undo_stack, self.redo_stack)
                    if action == "undo"
                    else (self.redo_stack, self.undo_stack)
                )
                if not src:
                    raise SessionError(f"Nothing to {action}.")
                dst.append(previous)
                self._restore(src.pop())
                result = {
                    "done": False,
                    "observations": [
                        "Last edit undone." if action == "undo" else "Edit restored."
                    ],
                }
            elif action == "review_clue":
                if (
                    set(args) != {"action", "clue_id", "reviewed"}
                    or type(args["reviewed"]) is not bool
                ):
                    raise SessionError(
                        "review_clue needs clue_id and a boolean reviewed"
                    )
                if args["clue_id"] not in {
                    f"clue-{i+1}" for i in range(len(self.pad.case.clues))
                }:
                    raise SessionError("unknown clue")
                (self.reviewed.add if args["reviewed"] else self.reviewed.discard)(
                    args["clue_id"]
                )
                result = {
                    "done": False,
                    "observations": [
                        "Personal checklist updated. This does not evaluate the clue."
                    ],
                }
            elif action == "note":
                if (
                    set(args) != {"action", "text"}
                    or not isinstance(args["text"], str)
                    or len(args["text"]) > 8192
                ):
                    raise SessionError("note needs text of at most 8192 characters")
                self.notebook = args["text"]
                result = {"done": False, "observations": ["Case note saved."]}
            elif action == "present":
                if set(args) != {"action"} or note is None:
                    raise SessionError("present needs a presentation note")
                result = {
                    "done": False,
                    "observations": ["Presentation note recorded."],
                }
            else:
                validate_tool_action(args, self.pad)
                result = apply_structured_action(
                    self.pad, args, self.allow_check, self.reward_config
                )
            if (
                action not in ("undo", "redo", "board", "check", "present", "submit")
                and self._snapshot() != previous
            ):
                self.undo_stack.append(previous)
                self.redo_stack.clear()
            self.done = bool(result.get("done"))
            if self.done:
                self.terminal = deepcopy(result)
            self.revision += 1
            event = {
                "index": self.revision,
                "action": deepcopy(args),
                "note": note,
                "source": source if source in ("human", "tool") else "tool",
                "message": result.get("observations", ["Recorded."])[-1],
            }
            self.events.append(event)
            self.pending_note = deepcopy(note) if action == "present" else None
            state = self.observe()
            self.frames.append(deepcopy(state))
            return {"result": result, "observation": state}

    def export_trace(self):
        return {
            "schema": "murdoku.trace/1",
            "case_id": self.entry.slug,
            "source": {
                "kind": "recorded_tool_calls",
                "label": "Local session; model provenance is not asserted",
            },
            "steps": deepcopy(self.events),
        }
