def emojis_to_altcode(emoji_array):
    for emoji in emoji_array:
        try:
            unicode = "{:X}".format(ord(emoji))
            print(f"'&#{int(unicode, 16)}', //{emoji}")
        except Exception:
            continue


emojiArray = [
    "😀",
    "😎",
    "😜",
    "😂",
    "😍",
    "🥳",
    "🤖",
    "🚀",
    "💼",
    "🧐",
    "🌈",
    "🔥",
    "💯",
    "🎉",
    "🚂",
    "🌟",
    "🍕",
    "🎸",
    "🍩",
    "👽",
    "🎈",
    "🍺",
    "🍕",
    "🤟",
    "🤘",
    "🕺",
    "🎃",
    "🌊",
    "🔍",
    "🎲",
    "📅",
    "🕵️‍♂️",
    "💡",
    "🚦",
    "🌌",
    "🍀",
    "🏰",
    "🚴‍♂️",
    "🍣",
    "🍔",
    "🎤",
    "🎹",
    "🎭",
    "🌮",
    "🚁",
    "🛸",
    "🎡",
    "🎢",
    "🚀",
    "🚁",
    "🏇",
    "🌵",
    "🗿",
    "🎰",
    "🕰️",
    "📚",
    "📡",
    "🔮",
    "🏆",
    "🍹",
    "🍻",
    "🍷",
    "🍭",
    "🍬",
    "🚁",
    "🎲",
    "🎮",
    "🎳",
    "🏓",
    "🎯",
    "🏸",
    "🎱",
    "🎨",
    "🎤",
    "🎧",
    "🎼",
    "🎸",
    "🥁",
    "🎷",
    "🎺",
    "🎻",
    "🏮",
    "📸",
    "📽️",
    "🎞️",
    "🎥",
    "📡",
    "📺",
    "📻",
    "🎙️",
    "📰",
    "🗞️",
    "📈",
    "📉",
    "🗂️",
    "🗄️",
    "🗑️",
    "🔑",
    "🗝️",
    "🔨",
    "⚖️",
    "🛡️",
    "🔧",
    "🔩",
    "🔗",
    "💉",
    "🏹",
    "🔫",
    "💣",
    "🔪",
    "🚬",
    "💊",
    "💈",
    "💰",
    "💳",
    "🛢️",
    "💎",
    "🔔",
    "💡",
    "🚽",
    "🚿",
    "🛁",
    "🚪",
    "🛋️",
    "🛌",
    "🖼️",
    "🛍️",
    "🛒",
    "🎁",
    "🎈",
    "🎀",
    "🎊",
    "🎉",
    "🎎",
    "🏮",
    "😀",
    "😃",
    "😄",
    "😁",
    "😆",
    "😅",
    "😂",
    "🤣",
    "😊",
    "😇",
    "🙂",
    "🙃",
    "😉",
    "😌",
    "😍",
    "🥰",
    "😘",
    "😗",
    "😙",
    "😚",
    "😋",
    "😛",
    "😜",
    "🤪",
    "😝",
    "🤑",
    "🤗",
    "🤭",
    "🤫",
    "🤔",
    "🤐",
    "🤨",
    "😐",
    "😑",
    "😶",
    "😏",
    "😒",
    "🙄",
    "😬",
    "🤥",
    "😌",
    "😔",
    "😪",
    "🤤",
    "😴",
    "😷",
    "🤒",
    "🤕",
    "🤢",
    "🤮",
    "🤧",
    "😵",
    "🤯",
    "🤠",
    "🥳",
    "😎",
    "🤓",
    "🧐",
    "😕",
    "😟",
    "🙁",
    "☹️",
    "😮",
    "😯",
    "😲",
    "😳",
    "🥺",
    "😦",
    "😧",
    "😨",
    "😰",
    "😥",
    "😢",
    "😭",
    "😱",
    "😖",
    "😣",
    "😞",
    "😓",
    "😩",
    "😫",
    "😤",
    "😡",
    "😠",
    "🤬",
    "😈",
    "👿",
    "💀",
    "💩",
    "🤡",
    "👹",
    "👺",
    "👻",
    "👽",
    "👾",
    "🤖",
    "😺",
    "😸",
    "😹",
    "😻",
    "😼",
    "😽",
    "🙀",
    "😿",
    "😾",
    "👐",
    "🙌",
    "👏",
    "🙏",
    "🤲",
    "🤝",
    "🤞",
    "🤟",
    "🤘",
    "🤙",
    "👈",
    "👉",
    "👆",
    "🖕",
    "👇",
    "☝️",
    "👊",
    "🤛",
    "🤜",
    "👌",
    "👍",
    "👎",
    "✊",
    "👊",
]
result = emojis_to_altcode(emojiArray)
