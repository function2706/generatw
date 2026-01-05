import errno
import inspect
import re
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import Any, Dict

import pyperclip


class Season(Enum):
    spring = auto()
    summer = auto()
    autumn = auto()
    winter = auto()


class Weather(Enum):
    sunny = auto()
    cloudy = auto()
    rainy = auto()
    snowy = auto()
    foggy = auto()


class Vibe(Enum):
    normal = auto()
    good = auto()
    bad = auto()


def search_regex(s: str, regex: str, gridx: int = 1) -> str:
    m = re.search(regex, s, flags=re.MULTILINE)
    if not m:
        raise OSError(errno.EINVAL, f'By "{regex}".')
    return m.group(gridx)


@dataclass
class Stats:
    @dataclass
    class Character:
        name: str = ""
        vibe: Vibe = Vibe.normal
        affection: int = 0
        trust: int = 0
        frustration: int = 0
        angry: int = 0
        in_heat: bool = 0
        mood: int = 0
        rationality: int = 0
        upper: str = ""
        upper_state: str = ""
        lower: str = ""
        lower_state: str = ""

        @classmethod
        def make(cls, clipboard: str):
            def make_name() -> str:
                return search_regex(clipboard, r"^(.+?)\s*(?:（[^）]+）)?\s*\(好感度")

            def make_vibe() -> Vibe:
                match = search_regex(clipboard, r"^.+?\s*(?:（([^）]+)）)?\s*\(好感度")
                if match == "ご機嫌":
                    return Vibe.good
                elif match == "フキゲン":
                    return Vibe.bad
                else:
                    return Vibe.normal

            def make_affection() -> int:
                return int(search_regex(clipboard, r"好感度:\s*[a-zA-Z]+\s*(\d+)"))

            def make_trust() -> int:
                return int(search_regex(clipboard, r"信頼度:\s*[a-zA-Z]+\s*(\d+)"))

            def make_frustration() -> int:
                return int(search_regex(clipboard, r"欲求不満度:\s*(\d+)％"))

            def make_angry() -> int:
                match = search_regex(clipboard, r"(?:怒り:\s*(！*)|怒)")
                return 6 if match is None else len(match)

            def make_in_heat() -> bool:
                try:
                    return True if search_regex(clipboard, r"発情中", 0) is not None else False
                except Exception:
                    return False

            def make_mood() -> int:
                match = search_regex(clipboard, r"(ムード:\s*(❤*)|OverDrive!!)")
                return 6 if match is None else len(match)

            def make_rationality() -> int:
                match = search_regex(clipboard, r"(理性:\s*(★*)|LimitBreak!!)")
                return -1 if match is None else len(match)

            def make_upper() -> str:
                return search_regex(clipboard, r"【上半身】\s*([^\s]*)").strip()

            def make_upper_state() -> str:
                return search_regex(clipboard, r"【上半身】\s*[^\s]*\s*([^\s]*)").strip()

            def make_lower() -> str:
                return search_regex(clipboard, r"【下半身】\s*([^\s]*)").strip()

            def make_lower_state() -> str:
                return search_regex(clipboard, r"【下半身】\s*[^\s]*\s*([^【]*)").strip()

            return cls(
                name=make_name(),
                vibe=make_vibe(),
                affection=make_affection(),
                trust=make_trust(),
                frustration=make_frustration(),
                angry=make_angry(),
                in_heat=make_in_heat(),
                mood=make_mood(),
                rationality=make_rationality(),
                upper=make_upper(),
                upper_state=make_upper_state(),
                lower=make_lower(),
                lower_state=make_lower_state(),
            )

    @dataclass
    class Meta:
        season: Season = Season.spring
        hour: int = 0
        minute: int = 0
        prefecture: str = ""
        address: str = ""
        cleanliness: str = ""
        weather: Weather = Weather.sunny
        rainbow: bool = False
        temperature: float = 0

        @classmethod
        def make(cls, clipboard: str):
            def make_season() -> Season:
                match = search_regex(clipboard, r"([春夏秋冬])の月")
                if match == "春":
                    return Season.spring
                elif match == "夏":
                    return Season.summer
                elif match == "秋":
                    return Season.autumn
                elif match == "冬":
                    return Season.winter
                else:
                    raise OSError(errno.EINVAL, inspect.currentframe().f_code.co_name)

            def make_hour() -> int:
                return int(search_regex(clipboard, r"(\d+)時"))

            def make_minute() -> int:
                return int(search_regex(clipboard, r"(\d+)分"))

            def make_address() -> str:
                try:
                    return search_regex(clipboard, r"(\S+)\s+清潔度:")
                except Exception:
                    return ""

            def make_cleanliness() -> str:
                try:
                    return search_regex(clipboard, r"清潔度:(\S+)")
                except Exception:
                    return ""

            def make_weather() -> Weather:
                match = re.search(
                    r"(晴れ|快晴|薄曇|曇り|雨|大雨|霧雨|霧|雪|吹雪|細雪|霧雪|みぞれ|あられ)",
                    clipboard,
                )
                if not match:
                    raise OSError(errno.EINVAL, inspect.currentframe().f_code.co_name)
                val = match.group(1)
                if "晴" in val:
                    return Weather.sunny
                elif "曇" in val:
                    return Weather.cloudy
                elif "雨" in val:
                    return Weather.rainy
                elif "霧" in val:
                    return Weather.foggy
                else:
                    return Weather.rainy

            def make_rainbow() -> bool:
                return False

            def make_temperature() -> float:
                match = re.search(r"気温(\S+)℃", clipboard)
                if not match:
                    raise OSError(errno.EINVAL, inspect.currentframe().f_code.co_name)
                return float(match.group(1))

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

    character: Character
    meta: Meta

    @classmethod
    def make(cls, clipboard: str):
        character_lc = Stats.Character.make(clipboard)
        meta_lc = Stats.Meta.make(clipboard)
        return cls(character=character_lc, meta=meta_lc)

    def todict(self) -> Dict[str, Any]:
        return asdict(self)


clipboard = pyperclip.paste()

a = Stats.make(clipboard)
print(a.todict())
