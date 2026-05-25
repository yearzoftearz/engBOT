import anthropic
import os
import json
from bot.models.database import LearningMode


client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODE_CONTEXT = {
    LearningMode.GENERAL: "balanced mix of literary, conversational, and cultural English",
    LearningMode.LITERARY: "literary and poetic language, drawing from classic and contemporary literature",
    LearningMode.MODERN_NATIVE: "casual modern native speech, slang, and contemporary idioms",
    LearningMode.BUSINESS: "professional and business English, corporate communication and leadership language",
    LearningMode.CINEMATIC: "film, TV, and cinematic language — dialogue, screenwriting, dramatic expression",
    LearningMode.INTELLECTUAL: "academic, philosophical, and essay-style English",
    LearningMode.MUSIC_CULTURE: "music, pop culture, and lyrical expression from various genres",
}

SYSTEM_PROMPT = """You are a world-class English language curator specializing in advanced, native-level English for C1–C2 learners.

Your role is to curate daily English intelligence packs that help sophisticated learners sound articulate, natural, emotionally precise, and culturally aware. You draw from real literature, film, music, and everyday native speech.

Rules:
- Never use fake quotes or fabricated cultural references — only real works
- If citing a quote, use clearly paraphrased or real verified quotes only
- Prefer collocations and phrases over isolated single words
- Keep language modern but not trivial
- Avoid beginner vocabulary
- Every cultural reference must use real, existing titles and artists
- Write at C1–C2 register throughout
- Never invent book titles, film titles, or song titles"""

PACK_PROMPT_TEMPLATE = """Generate a Daily English Intelligence Pack for advanced learners (C1–C2) in the mode: {mode_context}.

Return a JSON object with exactly this structure:
{{
  "expression": "the word, phrase, or collocation",
  "part_of_speech": "noun / verb phrase / idiom / collocation / etc.",
  "definition": "nuanced explanation in natural English (2–4 sentences, include emotional tone and register)",
  "collocations": ["collocation 1", "collocation 2", "collocation 3", "collocation 4"],
  "example_sentence": "one high-quality, context-rich, native-sounding sentence",
  "cultural_ref": {{
    "type": "film OR music OR literature",
    "title": "exact real title",
    "creator": "director / artist / author name",
    "usage": "brief note on how the expression connects to this work — paraphrase only, no invented quotes"
  }},
  "native_usage": [
    "short natural sentence 1",
    "short natural sentence 2",
    "short natural sentence 3",
    "short natural sentence 4"
  ],
  "contrast": {{
    "items": ["word/phrase A", "word/phrase B", "word/phrase C"],
    "explanation": "clear explanation of the subtle differences in meaning, tone, and register between these"
  }},
  "mini_task": "one specific, engaging writing prompt using today's expression"
}}

Choose an expression that is high-utility, emotionally or stylistically meaningful, and genuinely used by native speakers. Avoid the most common expressions — push toward the interesting middle ground between basic and obscure."""


async def generate_daily_pack(mode: str = LearningMode.GENERAL) -> dict:
    mode_context = MODE_CONTEXT.get(mode, MODE_CONTEXT[LearningMode.GENERAL])
    prompt = PACK_PROMPT_TEMPLATE.format(mode_context=mode_context)

    message = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    return json.loads(text)


async def generate_more_examples(expression: str) -> str:
    message = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Give 5 more diverse, native-sounding example sentences using "{expression}".
Each sentence should show a different context (professional, casual, emotional, literary, conversational).
Format: numbered list, no extra explanation."""
        }],
    )
    return message.content[0].text.strip()


async def generate_challenge(expression: str) -> str:
    message = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Create a short, creative writing challenge for the expression "{expression}".
The challenge should:
- Be specific and engaging
- Push the learner to use the expression in an original, personal way
- Take 3–5 minutes to complete
- Be appropriate for C1–C2 writers

Return only the challenge prompt, nothing else."""
        }],
    )
    return message.content[0].text.strip()
