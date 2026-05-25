from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def daily_pack_keyboard(expression: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("💾 Save", callback_data=f"save:{expression}"),
            InlineKeyboardButton("✅ I know this", callback_data=f"known:{expression}"),
        ],
        [
            InlineKeyboardButton("📖 More examples", callback_data=f"examples:{expression}"),
            InlineKeyboardButton("⚡ Challenge me", callback_data=f"challenge:{expression}"),
        ],
        [
            InlineKeyboardButton("🔄 Repeat later", callback_data=f"later:{expression}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def review_keyboard(expression: str, review_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✅ I know it", callback_data=f"review_known:{review_id}:{expression}"),
            InlineKeyboardButton("🔄 Review again", callback_data=f"review_again:{review_id}:{expression}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def mode_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🌐 General", callback_data="mode:general"),
            InlineKeyboardButton("📖 Literary", callback_data="mode:literary"),
        ],
        [
            InlineKeyboardButton("🗣 Modern Native", callback_data="mode:modern_native"),
            InlineKeyboardButton("💼 Business", callback_data="mode:business"),
        ],
        [
            InlineKeyboardButton("🎬 Cinematic", callback_data="mode:cinematic"),
            InlineKeyboardButton("🧠 Intellectual", callback_data="mode:intellectual"),
        ],
        [
            InlineKeyboardButton("🎵 Music & Culture", callback_data="mode:music_culture"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_keyboard(action: str, value: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm:{action}:{value}"),
            InlineKeyboardButton("❌ No", callback_data="cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
