import json
import re
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import Any, Dict

import pyperclip


def json_default(o):
    if isinstance(o, Enum):
        return o.name
    raise TypeError(f"{o.__class__.__name__} is not JSON serializable")


def dump_json(data: Dict, label: str) -> None:
    """
    指定の Dict を json 形式でダンプする

    Args:
        data (Dict): ダンプ対象
        label (str): 表示するラベル("label": {...})
    """
    print(f'"{label}":')
    print(json.dumps(data, ensure_ascii=False, indent=2, default=json_default))


class Season(Enum):
    spring = auto()
    summer = auto()
    autumn = auto()
    winter = auto()
    none = auto()


class Weather(Enum):
    sunny = auto()
    cloudy = auto()
    rainy = auto()
    snowy = auto()
    foggy = auto()
    none = auto()


class Vibe(Enum):
    normal = auto()
    good = auto()
    bad = auto()
    none = auto()


def search_regex(s: str, regex: str, gridx: int = 1) -> str:
    m = re.search(regex, s, flags=re.MULTILINE)
    if not m:
        print(f'No match with "{regex}".')
        return None
    return m.group(gridx)


@dataclass
class Character:
    name: str = ""
    vibe: Vibe = Vibe.none
    affection: int = -1
    trust: int = -1
    frustration: int = -1
    angry: int = -1
    in_heat: bool = -1
    mood: int = -1
    corruption: int = -1
    upper: str = ""
    upper_state: str = ""
    lower: str = ""
    lower_state: str = ""

    @classmethod
    def make(cls, clipboard: str):
        def make_name() -> str:
            match = search_regex(clipboard, r"^(.+?)\s*(?:（[^）]+）)?\s*\(好感度")
            return "" if match is None else match

        def make_vibe() -> Vibe:
            match = search_regex(clipboard, r"^.+?\s*(?:（([^）]+)）)?\s*\(好感度")
            if match is None:
                return Vibe.none
            elif match == "ご機嫌":
                return Vibe.good
            elif match == "フキゲン":
                return Vibe.bad
            else:
                return Vibe.normal

        def make_affection() -> int:
            match = search_regex(clipboard, r"好感度:\s*[a-zA-Z]+\s*(\d+)")
            return -1 if match is None else int(match)

        def make_trust() -> int:
            match = search_regex(clipboard, r"信頼度:\s*[a-zA-Z]+\s*(\d+)")
            return -1 if match is None else int(match)

        def make_frustration() -> int:
            match = search_regex(clipboard, r"欲求不満度:\s*(\d+)％")
            return -1 if match is None else int(match)

        def make_angry() -> int:
            match = search_regex(clipboard, r"怒り:\s*(！*)|怒", 0)
            if match is None:
                return -1
            elif match == "怒":
                return 6
            else:
                return len(match.replace("怒り:", "").strip())

        def make_in_heat() -> bool:
            return False if search_regex(clipboard, r"発情中", 0) is None else True

        def make_mood() -> int:
            match = search_regex(clipboard, r"ムード:\s*(OverDrive!!|❤*)")
            return -1 if match is None else 6 if match == "OverDrive!!" else len(match)

        def make_corruption() -> int:
            match = search_regex(clipboard, r"理性:\s*(LimitBreak!!|★*)")
            return -1 if match is None else 6 if match == "LimitBreak!!" else 5 - len(match)

        def make_upper() -> str:
            match = search_regex(clipboard, r"【上半身】\s*([^\s]*)")
            return "" if match is None else match.strip()

        def make_upper_state() -> str:
            match = search_regex(clipboard, r"【上半身】\s*[^\s]*\s*([^【]*)")
            return "" if match is None else match.strip()

        def make_lower() -> str:
            match = search_regex(clipboard, r"【下半身】\s*([^\s]*)")
            return "" if match is None else match.strip()

        def make_lower_state() -> str:
            match = search_regex(clipboard, r"【下半身】\s*[^\s]*\s*([^【=<]*)")
            return "" if match is None else match.strip()

        return cls(
            name=make_name(),
            vibe=make_vibe(),
            affection=make_affection(),
            trust=make_trust(),
            frustration=make_frustration(),
            angry=make_angry(),
            in_heat=make_in_heat(),
            mood=make_mood(),
            corruption=make_corruption(),
            upper=make_upper(),
            upper_state=make_upper_state(),
            lower=make_lower(),
            lower_state=make_lower_state(),
        )


@dataclass
class Meta:
    season: Season = Season.none
    hour: int = -1
    minute: int = -1
    address: str = ""
    cleanliness: str = ""
    weather: Weather = Weather.none
    rainbow: bool = False
    temperature: float = 0

    @classmethod
    def make(cls, clipboard: str):
        def make_season() -> Season:
            match = search_regex(clipboard, r"([春夏秋冬])の月")
            if match is None:
                return Season.none
            elif match == "春":
                return Season.spring
            elif match == "夏":
                return Season.summer
            elif match == "秋":
                return Season.autumn
            elif match == "冬":
                return Season.winter
            else:
                return Season.none

        def make_hour() -> int:
            match = search_regex(clipboard, r"(\d+)時")
            return -1 if match is None else int(match)

        def make_minute() -> int:
            match = search_regex(clipboard, r"(\d+)分")
            return -1 if match is None else int(match)

        def make_address() -> str:
            match = search_regex(clipboard, r"(\S+)\s+清潔度:")
            if match is not None:
                return match
            match = search_regex(clipboard, r"(\S+)\s+\(到着")
            if match is not None:
                return match
            match = search_regex(clipboard, r"\S+\s+-\s(\S+)\s-")
            if match is not None:
                return match
            match = search_regex(clipboard, r"\]\s*([^\s\[\-、=]+)\s*\[")
            if match is not None:
                return match
            return ""

        def make_cleanliness() -> str:
            match = search_regex(clipboard, r"清潔度:(\S+)")
            return "" if match is None else match

        def make_weather() -> Weather:
            match = search_regex(
                clipboard,
                r"(晴れ|快晴|薄曇|曇り|雨|大雨|霧雨|霧|雪|吹雪|細雪|霧雪|みぞれ|あられ)",
            )
            if match is None:
                return Weather.none
            elif "晴" in match:
                return Weather.sunny
            elif "曇" in match:
                return Weather.cloudy
            elif "雨" in match:
                return Weather.rainy
            elif "霧" in match:
                return Weather.foggy
            else:
                return Weather.rainy

        def make_rainbow() -> bool:
            return False

        def make_temperature() -> float:
            match = search_regex(clipboard, r"気温(\S+)℃")
            return -1 if match is None else float(match)

        return cls(
            season=make_season(),
            hour=make_hour(),
            minute=make_minute(),
            address=make_address(),
            cleanliness=make_cleanliness(),
            weather=make_weather(),
            rainbow=make_rainbow(),
            temperature=make_temperature(),
        )


@dataclass
class Stats:
    character: Character
    meta: Meta

    @classmethod
    def make(cls, clipboard: str):
        character_lc = Character.make(clipboard)
        meta_lc = Meta.make(clipboard)
        return cls(character=character_lc, meta=meta_lc)

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


clipboard = pyperclip.paste()

a = Stats.make(clipboard)
# dump_json(a.todict(), "test")
print(a.todict())
