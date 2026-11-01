"""Validate model-proposed search changes before committing any session state.

Only explicit, independently parsed structured facts are accepted as hard
filters. Semantic preferences are handled separately, never as hard filters.
"""

import re

from backend.services.recommendation import CRITERIA_FIELDS, parse_criteria

AMBIGUOUS = re.compile(
    r"如果|假如|假設|也許|可能|朋友|同學|同事|別人|不是|不要|不想|不考慮|不需要"
)

POSITIVE_CLAUSE = {
    "delivery_mode": r"(?:我)?(?:想|想要|希望|希望能|要|只要|只能|偏好|選擇)?(?:上|找)?(?:線上|遠距|實體|面授)(?:課|課程|上課|授課|教學)?",
    "max_price": r"(?:我的)?(?:預算(?:改成|改為|調整為|最多|上限)?|每堂|一堂|最多|上限)?\s*\d{3,5}\s*元?\s*(?:以下|以內|內|最多|上限)",
    "level": r"(?:我)?(?:是|目前是|程度是|程度為)?(?:完全沒學過|零基礎|沒學過|初學|新手|入門|初階|初級|中階|中級|進階|高階|高級)",
    "style": r"(?:我)?(?:只想|只要|一定要)(?:學|彈)?(?:古典|流行|爵士|即興|兒童)(?:鋼琴)?",
    "region": r"(?:我在|地區是|地區為|限|只限)?(?:台|臺|新北|桃園|高雄|基隆|新竹|嘉義|彰化|苗栗|南投|雲林|屏東|宜蘭|花蓮)[\u4e00-\u9fff]{1,8}",
    "time_slot": r"(?:我)?(?:希望|只能|偏好)?(?:平日上午|平日下午|平日晚上|週末上午|週末下午|週末晚上|平日|週末)(?:有空|上課)?",
}


class InvalidPlan(ValueError):
    """A model proposed an ungrounded or unsupported state change."""


def apply_changes(previous: dict, message: str, changes: list[dict]) -> dict:
    proposed = dict(previous)
    seen = set()
    for change in changes:
        if not isinstance(change, dict):
            raise InvalidPlan("invalid change")
        field = change.get("field")
        quote = change.get("quote")
        if (
            field not in CRITERIA_FIELDS
            or field in seen
            or not isinstance(quote, str)
            or not quote.strip()
            or message.count(quote) != 1
        ):
            raise InvalidPlan("ungrounded or duplicate change")
        parsed = parse_criteria(quote)
        whole = parse_criteria(message)
        value = change.get("value")
        if AMBIGUOUS.search(message):
            raise InvalidPlan("ambiguous context")
        if value is None and field == "max_price":
            start = message.find(quote)
            prefix = message[max(0, start - 4) : start]
            clear = re.fullmatch(
                r"(?:預算|價格)(?:不限|不設上限|不限制)|取消(?:預算|價格)(?:限制|上限)",
                quote,
            )
            clause = next((part.strip() for part in re.split(r"[，,。；;！!\n]", message) if quote in part), "")
            if clear and re.fullmatch(re.escape(quote) + r"(?:[，,]其他不變)?[。！!]?$", message.strip()) and not re.search(r"不|非|沒有|別", prefix):
                proposed[field] = None
                seen.add(field)
                continue
        if "?" in message or "？" in message:
            raise InvalidPlan("question is not a confirmed constraint")
        clause = next((part.strip() for part in re.split(r"[，,。；;！!\n]", message) if quote in part), "")
        if not re.fullmatch(POSITIVE_CLAUSE[field], clause):
            raise InvalidPlan("constraint needs confirmation")
        if field == "region":
            normalized_clause = clause.replace("臺", "台")
            if not isinstance(value, str) or normalized_clause not in {value, "我在" + value, "地區是" + value, "地區為" + value, "限" + value, "只限" + value}:
                raise InvalidPlan("location needs confirmation")
        if (
            field not in parsed
            or parsed[field] != value
            or type(parsed[field]) is not type(value)
            or field not in whole
            or whole[field] != value
        ):
            raise InvalidPlan("unverifiable change")
        proposed[field] = value
        seen.add(field)
    return proposed
