import re
from dataclasses import dataclass


@dataclass
class EasyToken:
    token: str = ""
    weight: float = ""

    @classmethod
    def make(cls, original_token: str):
        m = re.fullmatch(r"\(?(\w+)(?::([0-9.]+))?\)?", original_token)
        if not m:
            return cls("", "")
        token, weight = m.groups()
        return cls(token=token, weight=1.0 if weight is None else float(weight))


et = EasyToken.make("hoge")
print(f"{et.token}:{et.weight}")
