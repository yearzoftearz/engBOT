from typing import Any


CULTURAL_TYPE_EMOJI = {
    "film": "🎬",
    "music": "🎵",
    "literature": "📚",
}

MODE_LABELS = {
    "general": "General",
    "literary": "📖 Literary",
    "modern_native": "🗣 Modern Native",
    "business": "💼 Business",
    "cinematic": "🎬 Cinematic",
    "intellectual": "🧠 Intellectual",
    "music_culture": "🎵 Music & Culture",
}


def format_daily_pack(pack: dict[str, Any], mode: str = "general") -> str:
    exp = pack.get("expression", "")
    pos = pack.get("part_of_speech", "")
    definition = pack.get("definition", "")
    collocations = pack.get("collocations", [])
    example = pack.get("example_sentence", "")
    cultural_ref = pack.get("cultural_ref", {})
    native_usage = pack.get("native_usage", [])
    contrast = pack.get("contrast", {})
    mini_task = pack.get("mini_task", "")

    mode_label = MODE_LABELS.get(mode, "General")
    cult_emoji = CULTURAL_TYPE_EMOJI.get(cultural_ref.get("type", ""), "🌐")

    colloc_lines = "\n".join(f"  • {c}" for c in collocations)
    native_lines = "\n".join(f"  • {s}" for s in native_usage)

    contrast_items = contrast.get("items", [])
    contrast_vs = " vs ".join(f"*{i}*" for i in contrast_items)
    contrast_explanation = contrast.get("explanation", "")

    lines = [
        f"🧠 *Daily English Intelligence Pack*",
        f"_{mode_label} Mode_",
        "",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"✦ *Expression of the Day*",
        f"*{exp}* _{pos}_",
        "",
        f"📌 *Definition*",
        definition,
        "",
        f"🔗 *Collocations & Patterns*",
        colloc_lines,
        "",
        f"✍️ *Example*",
        f"_{example}_",
        "",
        f"{cult_emoji} *Cultural Reference*",
    ]

    if cultural_ref:
        c_type = cultural_ref.get("type", "").capitalize()
        c_title = cultural_ref.get("title", "")
        c_creator = cultural_ref.get("creator", "")
        c_usage = cultural_ref.get("usage", "")
        lines.append(f"*{c_type}:* {c_title} — {c_creator}")
        if c_usage:
            lines.append(f"_{c_usage}_")

    lines += [
        "",
        f"🗣 *Native Usage*",
        native_lines,
        "",
        f"⚡ *Contrast*",
        contrast_vs,
        contrast_explanation,
        "",
        f"✏️ *Mini Task*",
        mini_task,
        "",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)


def format_saved_list(vocab_items: list) -> str:
    if not vocab_items:
        return "You haven't saved any expressions yet.\n\nUse the *Save* button on any daily pack to build your collection."

    lines = ["📚 *Your Saved Expressions*", ""]
    for i, item in enumerate(vocab_items, 1):
        known_tag = " ✓" if item.known else ""
        lines.append(f"{i}. *{item.expression}*{known_tag}")
        if item.definition_snippet:
            snippet = item.definition_snippet[:80] + "…" if len(item.definition_snippet) > 80 else item.definition_snippet
            lines.append(f"   _{snippet}_")

    lines += ["", f"Total: {len(vocab_items)} expressions saved"]
    return "\n".join(lines)


def format_review_pack(expression: str, definition_snippet: str | None, times_seen: int) -> str:
    lines = [
        "🔄 *Spaced Repetition Review*",
        "",
        f"Do you remember this expression?",
        "",
        f"*{expression}*",
    ]
    if definition_snippet:
        lines += ["", f"_{definition_snippet}_"]
    lines += [
        "",
        f"You've seen this {times_seen} time{'s' if times_seen != 1 else ''}.",
        "",
        "How well do you know it?",
    ]
    return "\n".join(lines)
