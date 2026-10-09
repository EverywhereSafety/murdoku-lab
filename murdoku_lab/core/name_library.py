"""Preset display names indexed by the canonical character initial."""

from __future__ import annotations

import random
from dataclasses import replace

from .theme import canonical_theme

# Each column supplies alternatives for one initial, A–Z.
FEMININE = dict(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (
            ("Alice", "Amelia"),
            ("Beatrice", "Bella"),
            ("Clara", "Chloe"),
            ("Diana", "Daisy"),
            ("Elena", "Emma"),
            ("Flora", "Freya"),
            ("Grace", "Gemma"),
            ("Hannah", "Hazel"),
            ("Iris", "Isabel"),
            ("Julia", "Jasmine"),
            ("Kira", "Katherine"),
            ("Lena", "Lucy"),
            ("Maya", "Mara"),
            ("Nora", "Naomi"),
            ("Olivia", "Opal"),
            ("Priya", "Paula"),
            ("Quinn", "Queenie"),
            ("Rosa", "Ruby"),
            ("Sofia", "Sara"),
            ("Tessa", "Tara"),
            ("Uma", "Ursula"),
            ("Vera", "Violet"),
            ("Wendy", "Willow"),
            ("Xena", "Ximena"),
            ("Yara", "Yasmin"),
            ("Zoe", "Zara"),
        ),
    )
)
MASCULINE = dict(
    zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (
            ("Adrian", "Arthur"),
            ("Benjamin", "Bruno"),
            ("Caleb", "Carlos"),
            ("Daniel", "Dante"),
            ("Elias", "Ethan"),
            ("Felix", "Finn"),
            ("Gabriel", "George"),
            ("Henry", "Hugo"),
            ("Ivan", "Isaac"),
            ("Jonah", "Julian"),
            ("Kai", "Kieran"),
            ("Leo", "Liam"),
            ("Marco", "Miles"),
            ("Noah", "Nico"),
            ("Oliver", "Oscar"),
            ("Pedro", "Philip"),
            ("Quentin", "Quincy"),
            ("Rafael", "Robin"),
            ("Samuel", "Simon"),
            ("Theo", "Tobias"),
            ("Umar", "Ulysses"),
            ("Victor", "Vincent"),
            ("Walter", "Wesley"),
            ("Xavier", "Xander"),
            ("Yusuf", "Yuri"),
            ("Zane", "Zachary"),
        ),
    )
)


def preset_theme(case, *, seed: int | None = None):
    """Name a cast reproducibly, keeping distinct initials equal to tool IDs.

    Explicit themes take precedence at the caller. No solution fields are read.
    Untagged characters can draw from either pool and use neutral pronouns.
    """
    rng = random.Random(seed if seed is not None else (case.seed or 0))
    names, pronouns = {}, {}
    for symbol in case.characters:
        if symbol not in FEMININE:
            raise ValueError(
                f"preset names require single-letter A–Z IDs, got {symbol!r}"
            )
        tags = case.tags.get(symbol, ())
        if "woman" in tags and "man" not in tags:
            pool, pronoun = FEMININE[symbol], "she"
        elif "man" in tags and "woman" not in tags:
            pool, pronoun = MASCULINE[symbol], "he"
        else:
            pool, pronoun = FEMININE[symbol] + MASCULINE[symbol], "they"
        names[symbol] = rng.choice(pool)
        pronouns[symbol] = pronoun
    theme = replace(
        canonical_theme(case), theme_id="preset-names", names=names, pronouns=pronouns
    )
    theme.validate(case)
    return theme
