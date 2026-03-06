import os
import sys
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any

import pyperclip
import yaml

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from common.functions import dump_json  # noqa: E402
from parser.prompter import Prompter  # noqa: E402

CORRECT_RESULT = {
    "CASE 'empty definition'": {"Empty-1: 'go'": {"SID": "main", "POS": [], "NEG": [], "REP": []}},
    "CASE 'ignition'": {
        "PrompterTest-1: 'foobarbaz'": {"SID": None, "POS": [], "NEG": [], "REP": []},
        "PrompterTest-2: 'main name: Hogemaru,'": {
            "SID": "main",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-3: 'main meta name: Fugami,weather: sunny,'": {
            "SID": "main",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "fugami", "weight": 1.2}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
    },
    "CASE 'match'": {
        "PrompterTest-1: 'main vibe: good,'": {
            "SID": "main",
            "POS": [{"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]}],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-2: 'sub vibe: good,'": {"SID": "sub", "POS": [], "NEG": [], "REP": []},
        "PrompterTest-3: 'main season: 02,name: Foota,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["name"],
                    "tokens": [{"token": "foota", "weight": 1.0}, {"token": "boy", "weight": 1.1}],
                },
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "winter", "weight": 1.0},
                        {"token": "cool", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {"path": ["name"], "tokens": [{"token": "barta", "weight": 1.0}]},
                {"path": ["season"], "tokens": [{"token": "scorching heat", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-4: 'main name: Hogemaru,name: Fugami,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["name"],
                    "tokens": [
                        {"token": "hogemaru", "weight": 1.0},
                        {"token": "fugami", "weight": 1.2},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
    },
    "CASE 'hit'": {
        "PrompterTest-1: 'meta weather: snowy,'": {
            "SID": "meta",
            "POS": [
                {"path": ["weather"], "tokens": [{"token": "cloudy", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common meta", "weight": 1.0}]},
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "snowy",
                    "pattern": "weather:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "meta",
                    "path": ["weather"],
                }
            ],
        },
        "PrompterTest-2: 'meta location: office,'": {
            "SID": "meta",
            "POS": [{"path": [], "tokens": [{"token": "common meta", "weight": 1.0}]}],
            "NEG": [],
            "REP": [
                {
                    "matched": "location: o",
                    "pattern": "location:\\s(.+?)",
                    "capturegrp": 0,
                    "screen_id": "meta",
                    "path": ["location"],
                }
            ],
        },
        "PrompterTest-3: 'sub like: Carrot,'": {
            "SID": "sub",
            "POS": [{"path": ["like"], "tokens": [{"token": "nothing", "weight": 1.0}]}],
            "NEG": [],
            "REP": [
                {
                    "matched": "Carrot",
                    "pattern": "like:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "sub",
                    "path": ["like"],
                }
            ],
        },
        "PrompterTest-4: 'sub ability: Toughness,'": {
            "SID": "sub",
            "POS": [],
            "NEG": [],
            "REP": [
                {
                    "matched": "Toughness",
                    "pattern": "ability:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "sub",
                    "path": ["ability"],
                }
            ],
        },
    },
    "CASE 'nest'": {
        "PrompterTest-1: 'main upper: T Shirt,lower: Pants,'": {
            "SID": "main",
            "POS": [
                {"path": ["fashion", "upper"], "tokens": [{"token": "t-shirt", "weight": 1.0}]},
                {"path": ["fashion", "lower"], "tokens": [{"token": "pants", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        }
    },
    "CASE 'capture'": {
        "PrompterTest-1: 'sub WoW!'": {
            "SID": "sub",
            "POS": [{"path": ["whole"], "tokens": [{"token": "WoW", "weight": 1.0}]}],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-2: 'sub ng: Dummy,'": {"SID": "sub", "POS": [], "NEG": [], "REP": []},
        "PrompterTest-3: 'sub grade: 1,'": {
            "SID": "sub",
            "POS": [{"path": ["grade"], "tokens": [{"token": "grade 1", "weight": 1.0}]}],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-4: 'sub grade: 2,'": {
            "SID": "sub",
            "POS": [{"path": ["grade"], "tokens": [{"token": "grade 2", "weight": 1.0}]}],
            "NEG": [],
            "REP": [],
        },
    },
    "CASE 'weight-tokens'": {
        "PrompterTest-1: 'main name: Foota,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["name"],
                    "tokens": [{"token": "foota", "weight": 1.0}, {"token": "boy", "weight": 1.1}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {"path": ["name"], "tokens": [{"token": "barta", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        }
    },
    "CASE 'default'": {
        "PrompterTest-1: 'meta weather: snowy,'": {
            "SID": "meta",
            "POS": [
                {"path": ["weather"], "tokens": [{"token": "cloudy", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common meta", "weight": 1.0}]},
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "snowy",
                    "pattern": "weather:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "meta",
                    "path": ["weather"],
                }
            ],
        },
        "PrompterTest-2: 'main season: 13,'": {
            "SID": "main",
            "POS": [
                {"path": ["season"], "tokens": [{"token": "ordinary", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {"path": ["season"], "tokens": [{"token": "storm", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [
                {
                    "matched": "13",
                    "pattern": "season:\\s([0-9]{2})",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "path": ["season"],
                }
            ],
        },
        "PrompterTest-3: 'main name: HogetaFugao,'": {
            "SID": "main",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "smith", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogetaFugao",
                    "pattern": "name:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "path": ["name"],
                }
            ],
        },
        "PrompterTest-4: 'main vitality: 1000,'": {
            "SID": "main",
            "POS": [{"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]}],
            "NEG": [
                {"path": ["vitality"], "tokens": [{"token": "special", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [
                {
                    "matched": "1000",
                    "pattern": "vitality:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "path": ["vitality"],
                }
            ],
        },
    },
    "CASE 'common'": {
        "PrompterTest-1: 'common1'": {
            "SID": "common1",
            "POS": [{"path": [], "tokens": [{"token": "common1", "weight": 1.0}]}],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-2: 'common2'": {
            "SID": "common2",
            "POS": [{"path": [], "tokens": [{"token": "common2", "weight": 1.0}]}],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-3: 'common3'": {
            "SID": "common3",
            "POS": [],
            "NEG": [{"path": [], "tokens": [{"token": "common3", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-4: 'common4'": {
            "SID": "common4",
            "POS": [{"path": [], "tokens": [{"token": "common4-pos", "weight": 1.0}]}],
            "NEG": [{"path": [], "tokens": [{"token": "common4-neg", "weight": 1.0}]}],
            "REP": [],
        },
    },
    "CASE 'ranges'": {
        "PrompterTest-1: 'main season: 04'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "spring", "weight": 1.0},
                        {"token": "cool", "weight": 1.0},
                        {"token": "H1", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "scorching heat", "weight": 1.0},
                        {"token": "H2", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-2: 'main season: 08'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "summer", "weight": 1.0}, {"token": "H1", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "cold", "weight": 1.0}, {"token": "H2", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-3: 'main season: 08'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "summer", "weight": 1.0}, {"token": "H1", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "cold", "weight": 1.0}, {"token": "H2", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-4: 'main season: 07'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "summer", "weight": 1.0}, {"token": "H1", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["season"],
                    "tokens": [{"token": "cold", "weight": 1.0}, {"token": "H2", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-5: 'main season: 01'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "winter", "weight": 1.1},
                        {"token": "snow", "weight": 1.0},
                        {"token": "cool", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {"path": ["season"], "tokens": [{"token": "scorching heat", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-6: 'main season: 09'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "summer", "weight": 1.0},
                        {"token": "cool", "weight": 1.0},
                        {"token": "H1", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["season"],
                    "tokens": [
                        {"token": "cold", "weight": 1.0},
                        {"token": "scorching heat", "weight": 1.0},
                        {"token": "H2", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-7: 'main season: 13'": {
            "SID": "main",
            "POS": [
                {"path": ["season"], "tokens": [{"token": "ordinary", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {"path": ["season"], "tokens": [{"token": "storm", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [
                {
                    "matched": "13",
                    "pattern": "season:\\s([0-9]{2})",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "path": ["season"],
                }
            ],
        },
        "PrompterTest-8: 'sub rwd: c,'": {
            "SID": "sub",
            "POS": [],
            "NEG": [],
            "REP": [
                {
                    "matched": "c",
                    "pattern": "rwd:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "sub",
                    "path": ["ranges without default"],
                }
            ],
        },
    },
    "CASE 'intervals'": {
        "PrompterTest-1: 'main vitality: 100,'": {
            "SID": "main",
            "POS": [
                {"path": ["vitality"], "tokens": [{"token": "perfect", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-2: 'main vitality: 50,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "low", "weight": 1.0},
                        {"token": "bad", "weight": 1.0},
                        {"token": "middle", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["vitality"],
                    "tokens": [{"token": "good", "weight": 1.0}, {"token": "high", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-3: 'main vitality: 95,'": {
            "SID": "main",
            "POS": [
                {"path": ["vitality"], "tokens": [{"token": "perfect", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-4: 'main vitality: 20,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["vitality"],
                    "tokens": [{"token": "low", "weight": 1.0}, {"token": "bad", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "good", "weight": 1.0},
                        {"token": "high", "weight": 1.0},
                        {"token": "ok", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-5: 'main vitality: 30,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["vitality"],
                    "tokens": [{"token": "low", "weight": 1.0}, {"token": "bad", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "good", "weight": 1.0},
                        {"token": "high", "weight": 1.0},
                        {"token": "ok", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-6: 'main vitality: 20,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["vitality"],
                    "tokens": [{"token": "low", "weight": 1.0}, {"token": "bad", "weight": 1.0}],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "good", "weight": 1.0},
                        {"token": "high", "weight": 1.0},
                        {"token": "ok", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-7: 'main vitality: 40,'": {
            "SID": "main",
            "POS": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "low", "weight": 1.0},
                        {"token": "bad", "weight": 1.0},
                        {"token": "middle", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]},
            ],
            "NEG": [
                {
                    "path": ["vitality"],
                    "tokens": [
                        {"token": "good", "weight": 1.0},
                        {"token": "high", "weight": 1.0},
                        {"token": "ok", "weight": 1.0},
                    ],
                },
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [],
        },
        "PrompterTest-8: 'main vitality: 1000,'": {
            "SID": "main",
            "POS": [{"path": [], "tokens": [{"token": "common main positive", "weight": 1.0}]}],
            "NEG": [
                {"path": ["vitality"], "tokens": [{"token": "special", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "common main negative", "weight": 1.0}]},
            ],
            "REP": [
                {
                    "matched": "1000",
                    "pattern": "vitality:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "main",
                    "path": ["vitality"],
                }
            ],
        },
        "PrompterTest-9: 'sub iwd: 100,'": {
            "SID": "sub",
            "POS": [],
            "NEG": [],
            "REP": [
                {
                    "matched": "100",
                    "pattern": "iwd:\\s(.+?),",
                    "capturegrp": 1,
                    "screen_id": "sub",
                    "path": ["intervals without default"],
                }
            ],
        },
    },
    "CASE 'import'": {
        "PrompterTest-1: 'import_src NAME:Hogemaru'": {
            "SID": "import_src",
            "POS": [
                {"path": ["partner", "name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-2: 'import_src NAME:HogeFuga'": {
            "SID": "import_src",
            "POS": [
                {"path": ["partner", "name"], "tokens": [{"token": "zero", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogeFuga",
                    "pattern": "NAME:(.+)",
                    "capturegrp": 1,
                    "screen_id": "import_src",
                    "path": ["partner", "name"],
                }
            ],
        },
        "PrompterTest-3: 'import_dst1 NAME-Fugami'": {
            "SID": "import_dst1",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "fugami", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-4: 'import_dst1 NAME-HogeFuga'": {
            "SID": "import_dst1",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "alice", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogeFuga",
                    "pattern": "NAME-(.+)",
                    "capturegrp": 1,
                    "screen_id": "import_dst1",
                    "path": ["name"],
                }
            ],
        },
        "PrompterTest-5: 'import_dst2 Name>Hogemaru'": {
            "SID": "import_dst2",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-6: 'import_dst2 Name>HogeFuga'": {
            "SID": "import_dst2",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "bob", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogeFuga",
                    "pattern": "Name>(.+)",
                    "capturegrp": 1,
                    "screen_id": "import_dst2",
                    "path": ["name"],
                }
            ],
        },
        "PrompterTest-7: 'import_dst3 name:Hogemaru'": {
            "SID": "import_dst3",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-8: 'import_dst3 name:HogeFuga'": {
            "SID": "import_dst3",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "cate", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogeFuga",
                    "pattern": "name:(.+)",
                    "capturegrp": 1,
                    "screen_id": "import_dst3",
                    "path": ["name"],
                }
            ],
        },
        "PrompterTest-9: 'import_dst4 name:Hogemaru'": {
            "SID": "import_dst4",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "hogemaru", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-10: 'import_dst4 name:HogeFuga'": {
            "SID": "import_dst4",
            "POS": [
                {"path": ["name"], "tokens": [{"token": "doe", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [
                {
                    "matched": "HogeFuga",
                    "pattern": "name:(.+)",
                    "capturegrp": 1,
                    "screen_id": "import_dst4",
                    "path": ["name"],
                }
            ],
        },
        "PrompterTest-11: 'import_dst3 flag'": {
            "SID": "import_dst3",
            "POS": [
                {"path": ["flag"], "tokens": [{"token": "flag is true", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
        "PrompterTest-12: 'import_dst4 flag'": {
            "SID": "import_dst4",
            "POS": [
                {"path": ["flag"], "tokens": [{"token": "flag is true", "weight": 1.0}]},
                {"path": [], "tokens": [{"token": "import common pos", "weight": 1.0}]},
            ],
            "NEG": [{"path": [], "tokens": [{"token": "import common neg", "weight": 1.0}]}],
            "REP": [],
        },
    },
    "CASE 'recursive'": {
        "PrompterTest-1: 'recursive_plane [(foo1),(foo2)][(bar1),(bar2),(bar3)][(baz1)]'": {
            "SID": "recursive",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-2: 'recursive_plane [(foo4)]'": {
            "SID": "recursive",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [{"token": "foobar", "weight": 1.0}],
                }
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "foo4",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "recursive",
                    "path": ["brackets_parentheses", "parentheses"],
                }
            ],
        },
        "PrompterTest-3: 'recursive_plane {(foo1),(foo2)}{(bar1),(bar2),(bar3)}{(baz1)}'": {
            "SID": "recursive",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-4: 'recursive_import <(foo1),(foo2)><(bar1),(bar2),(bar3)><(baz1)>'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
                {
                    "path": ["parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "(foo1),(foo2)",
                    "pattern": "<([^<>]+?)>",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["angles"],
                },
                {
                    "matched": "(bar1),(bar2),(bar3)",
                    "pattern": "<([^<>]+?)>",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["angles"],
                },
                {
                    "matched": "(baz1)",
                    "pattern": "<([^<>]+?)>",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["angles"],
                },
            ],
        },
        "PrompterTest-5: 'recursive_import [(foo1),(foo2)][(bar1),(bar2),(bar3)][(baz1)]'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
                {
                    "path": ["parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-6: 'recursive_import <(foo4)>'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [{"token": "foobar", "weight": 1.0}],
                }
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "foo4",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["brackets_parentheses", "parentheses"],
                },
                {
                    "matched": "(foo4)",
                    "pattern": "<([^<>]+?)>",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["angles"],
                },
                {
                    "matched": "foo4",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["parentheses"],
                },
            ],
        },
        "PrompterTest-7: 'recursive_import [(foo4)]'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["brackets_parentheses", "parentheses"],
                    "tokens": [{"token": "foobar", "weight": 1.0}],
                }
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "foo4",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["brackets_parentheses", "parentheses"],
                },
                {
                    "matched": "foo4",
                    "pattern": "\\(([^\\(\\)]+?)\\)",
                    "capturegrp": 1,
                    "screen_id": "recursive_import",
                    "path": ["parentheses"],
                },
            ],
        },
        "PrompterTest-8: 'recursive_import <foo1>,<foo2>,<bar1>,<bar2>,<bar3>,<baz1>'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["angles"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-9: 'recursive_import (foo1),(foo2),(bar1),(bar2),(bar3),(baz1)'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-10: 'recursive_import /(foo1),(foo2)//(bar1),(bar2),(bar3)//(baz1)/'": {
            "SID": "recursive_import",
            "POS": [
                {
                    "path": ["parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
                {
                    "path": ["slash_parentheses", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-11: 'recursive_recursive [{(foo1),foo2}{bar1,(bar2)}][{(bar3)},{baz1}]'": {
            "SID": "recursives",
            "POS": [
                {
                    "path": ["big", "middle", "small"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-12: 'recursive_name [(foo1),(foo2)][<bar1>,<bar2>,<bar3>][(baz1)]'": {
            "SID": "recursive_name",
            "POS": [
                {
                    "path": ["big", "child", "parentheses"],
                    "tokens": [
                        {"token": "foo1", "weight": 1.0},
                        {"token": "foo2", "weight": 1.0},
                        {"token": "baz1", "weight": 1.0},
                    ],
                },
                {
                    "path": ["big", "child", "angle"],
                    "tokens": [
                        {"token": "bar1", "weight": 1.0},
                        {"token": "bar2", "weight": 1.0},
                        {"token": "bar3", "weight": 1.0},
                    ],
                },
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-13: 'recursive_practice one's equip:[equip1][equip2][equip3][equip4]'": {
            "SID": "recursive_practice",
            "POS": [
                {
                    "path": ["equip", "equip_parts"],
                    "tokens": [
                        {"token": "equip1", "weight": 1.0},
                        {"token": "equip2", "weight": 1.0},
                        {"token": "equip3", "weight": 1.0},
                        {"token": "equip4", "weight": 1.0},
                    ],
                }
            ],
            "NEG": [],
            "REP": [],
        },
        "PrompterTest-14: 'recursive_report one's equip:[equip1][equip2][equip3][equip4]'": {
            "SID": "recursive_report",
            "POS": [
                {
                    "path": ["equip", "equip_parts_1"],
                    "tokens": [{"token": "equip1", "weight": 1.0}],
                },
                {
                    "path": ["equip", "equip_parts_2"],
                    "tokens": [{"token": "equip2", "weight": 1.0}],
                },
                {
                    "path": ["equip", "equip_parts_3"],
                    "tokens": [{"token": "equip3", "weight": 1.0}],
                },
                {
                    "path": ["equip", "equip_parts_4"],
                    "tokens": [{"token": "equip4", "weight": 1.0}],
                },
            ],
            "NEG": [],
            "REP": [
                {
                    "matched": "equip2",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_1"],
                },
                {
                    "matched": "equip3",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_1"],
                },
                {
                    "matched": "equip4",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_1"],
                },
                {
                    "matched": "equip1",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_2"],
                },
                {
                    "matched": "equip3",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_2"],
                },
                {
                    "matched": "equip4",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_2"],
                },
                {
                    "matched": "equip1",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_3"],
                },
                {
                    "matched": "equip2",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_3"],
                },
                {
                    "matched": "equip4",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_3"],
                },
                {
                    "matched": "equip1",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_4"],
                },
                {
                    "matched": "equip2",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_4"],
                },
                {
                    "matched": "equip3",
                    "pattern": "\\[([^\\[\\]]+?)\\]",
                    "capturegrp": 1,
                    "screen_id": "recursive_report",
                    "path": ["equip", "equip_parts_4"],
                },
            ],
        },
    },
}


def dict_diff(result: dict, correct: dict) -> dict[str, tuple[dict, dict]]:
    diff = {}
    all_keys = result.keys() | correct.keys()

    for k in all_keys:
        v1 = result.get(k)
        v2 = correct.get(k)
        if v1 != v2:
            diff[k] = ({"result": v1}, {"correct": v2})

    return diff


@dataclass
class PrompterDebugger:
    yamldict: dict = None
    prompter: Prompter = None

    @classmethod
    def make(cls, yamlpath: Path | str):
        obj = cls()
        obj.set(Path(yamlpath))
        return obj

    def set(self, yamlpath: Path):
        with open(yamlpath, "r", encoding="utf-8") as f:
            self.yamldict = yaml.safe_load(f)
        self.prompter = Prompter.make(yamlpath)

    def dump_yamldict(self) -> None:
        dump_json(self.yamldict, self.prompter.yamlpath.name.replace(".yaml", ""))

    def dump_normalized_yamldict(self) -> None:
        dump_json(
            self.prompter.todict(), f"normalized {self.prompter.yamlpath.name.replace('.yaml', '')}"
        )

    def debug_texts(self, texts: list[str], with_texts: bool = True) -> dict[str, dict[str, Any]]:
        """
        展開中 yaml について texts 内のテキストを順に適用する

        Args:
            texts (list[str]): テスト用テキスト
        """
        yamlname = self.prompter.yamlpath.name.replace(".yaml", "")
        result: dict[str, dict[str, Any]] = {}
        for i, text in enumerate(texts):
            try:
                prompt, reports = self.prompter.to_prompt(text)
                posneg = {
                    "SID": prompt.screen_id,
                    "POS": prompt.positive,
                    "NEG": prompt.negative,
                    "REP": reports,
                }
                if with_texts:
                    result[f"{yamlname}-{i + 1}: '{text}'"] = posneg
                else:
                    result[f"{yamlname}-{i + 1}"] = posneg
            except Exception as e:
                raise Exception(f"Error with '{text}'") from e
        return result

    def debug_cases(
        self, cases: dict[str, dict[Path | str, list[str]]]
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """
        cases の Path の yaml を毎度展開し, それに紐づくテキストを順に適用する\n
        最も外側の str はパス重複解決のためのラベル

        Args:
            testcases (dict[str, dict[Path | str, list[str]]]): テストケース
        """
        result: dict[str, dict[str, dict[str, Any]]] = {}
        for id, texts_n_paths in cases.items():
            result_by_texts = {}
            for yamlpath, texts in texts_n_paths.items():
                try:
                    self.set(Path(yamlpath))
                    result_by_texts = self.debug_texts(texts)
                except Exception as e:
                    raise Exception(f"Error on '{yamlpath}'") from e
            result[f"CASE '{id}'"] = result_by_texts
        return result

    def debug_clipboard(self) -> dict[str, dict[str, str]]:
        """
        展開中 yaml について現在のクリップボードのテキストを適用する
        """
        clipboard = pyperclip.paste()
        return self.debug_texts([clipboard], False)


def normalize(obj):
    if is_dataclass(obj):
        return normalize(asdict(obj))
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(i) for i in obj]
    if isinstance(obj, tuple):
        return [normalize(i) for i in obj]

    return obj


def debug_prompter() -> None:
    debugger = PrompterDebugger()
    result = debugger.debug_cases(
        {
            "empty definition": {
                "yamls/testyamls/Empty.yaml": ["go"]  # 空定義
            },
            "ignition": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "foobarbaz",  # Screen 発火なし
                    "main name: Hogemaru,",  # Screen 発火
                    "main meta name: Fugami,weather: sunny,",  # 複数 Screen 発火
                ]
            },
            "match": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "main vibe: good,",  # マッチなし, common あり
                    "sub vibe: good,",  # マッチなし, common なし
                    "main season: 02,name: Foota,",  # マッチ順序
                    "main name: Hogemaru,name: Fugami,",  # 複数マッチ
                ]
            },
            "hit": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "meta weather: snowy,",  # ヒットせず, default あり, common あり
                    "meta location: office,",  # ヒットせず, default なし, common あり
                    "sub like: Carrot,",  # ヒットせず, default あり, common なし
                    "sub ability: Toughness,",  # ヒットせず, default なし, common なし
                ]
            },
            "nest": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "main upper: T Shirt,lower: Pants,",  # 多階層 Rule
                ]
            },
            "capture": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "sub WoW!",  # 全体キャプチャ
                    "sub ng: Dummy,",  # キャプチャ範囲逸脱
                    "sub grade: 1,",  # キーが文字列の数値
                    "sub grade: 2,",  # キーが数値
                ]
            },
            "weight-tokens": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "main name: Foota,",  # 重み付き複数トークン
                ]
            },
            "default": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "meta weather: snowy,",  # 省略形
                    "main season: 13,",  # 両方記述
                    "main name: HogetaFugao,",  # positive のみ
                    "main vitality: 1000,",  # negative のみ
                ]
            },
            "common": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "common1",  # 省略形
                    "common2",  # positive のみ
                    "common3",  # negative のみ
                    "common4",  # 両方記述
                ]
            },
            "ranges": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "main season: 04",  # 省略形
                    "main season: 08",  # positive のみ
                    "main season: 08",  # negative のみ
                    "main season: 07",  # 両方記述 (positive)
                    "main season: 01",  # 両方記述 (negative)
                    "main season: 09",  # 複数ヒット
                    "main season: 13",  # ヒットせず, defaultあり
                    "sub rwd: c,",  # ヒットせず, default なし
                ]
            },
            "intervals": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "main vitality: 100,",  # 境界値
                    "main vitality: 50,",  # 省略形
                    "main vitality: 95,",  # positive のみ
                    "main vitality: 20,",  # negative のみ
                    "main vitality: 30,",  # 両方記述 (positive)
                    "main vitality: 20,",  # 両方記述 (negative)
                    "main vitality: 40,",  # 複数ヒット
                    "main vitality: 1000,",  # ヒットせず, defaultあり
                    "sub iwd: 100,",  # ヒットせず, default なし
                ]
            },
            "import": {
                "yamls/testyamls/PrompterTest.yaml": [
                    "import_src NAME:Hogemaru",  # 同一 Screen 内のインポート
                    "import_src NAME:HogeFuga",  # 同一 Screen 内のインポート (default)
                    "import_dst1 NAME-Fugami",  # 異なる Screen のインポート
                    "import_dst1 NAME-HogeFuga",  # 異なる Screen のインポート (default)
                    "import_dst2 Name>Hogemaru",  # 多段インポート
                    "import_dst2 Name>HogeFuga",  # 多段インポート (default)
                    "import_dst3 name:Hogemaru",  # pattern インポート
                    "import_dst3 name:HogeFuga",  # pattern インポート (default)
                    "import_dst4 name:Hogemaru",  # 多段 pattern インポート
                    "import_dst4 name:HogeFuga",  # 多段 pattern インポート (default)
                    "import_dst3 flag",  # pattern インポート (capturegrp 未定義)
                    "import_dst4 flag",  # 多段 pattern インポート (capturegrp 未定義)
                ]
            },
            "recursive": {
                "yamls/testyamls/PrompterTest.yaml": [
                    # 再帰標準機能
                    "recursive_plane [(foo1),(foo2)][(bar1),(bar2),(bar3)][(baz1)]",
                    # 再帰先 default
                    "recursive_plane [(foo4)]",
                    # 再帰構造のローカル import
                    "recursive_plane {(foo1),(foo2)}{(bar1),(bar2),(bar3)}{(baz1)}",
                    # 再帰構造のグローバル import
                    "recursive_import <(foo1),(foo2)><(bar1),(bar2),(bar3)><(baz1)>",
                    # 再帰構造のグローバル import (pattern 省略)
                    "recursive_import [(foo1),(foo2)][(bar1),(bar2),(bar3)][(baz1)]",
                    # 再帰構造のグローバル import, default
                    "recursive_import <(foo4)>",
                    # 再帰構造のグローバル import (pattern 省略), default
                    "recursive_import [(foo4)]",
                    # 再帰先 import
                    "recursive_import <foo1>,<foo2>,<bar1>,<bar2>,<bar3>,<baz1>",
                    # 再帰先 import (pattern 省略)
                    "recursive_import (foo1),(foo2),(bar1),(bar2),(bar3),(baz1)",
                    # 再帰先を別の再帰先 import で定義
                    "recursive_import /(foo1),(foo2)//(bar1),(bar2),(bar3)//(baz1)/",
                    # 2段以上の再帰
                    "recursive_recursive [{(foo1),foo2}{bar1,(bar2)}][{(bar3)},{baz1}]",
                    # 再帰先の名前が再帰・分岐
                    "recursive_name [(foo1),(foo2)][<bar1>,<bar2>,<bar3>][(baz1)]",
                    # 実践
                    "recursive_practice one's equip:[equip1][equip2][equip3][equip4]",
                    # レポート
                    "recursive_report one's equip:[equip1][equip2][equip3][equip4]",
                ]
            },
        }
    )
    dump_json(result, "debug")
    print("---------------------------------------------------------------------------")
    for key, test_result in result.items():
        correct_result = CORRECT_RESULT.get(key)
        if correct_result is None:
            print(f"NEW - {key}")
        else:
            normalized_test_result = normalize(test_result)
            if normalized_test_result == correct_result:
                print(f"OK  - {key}")
            else:
                print(f"NG  - {key}")
                dump_json(dict_diff(normalized_test_result, correct_result), "diff")


def print_yamldict(path: Path) -> None:
    debugger = PrompterDebugger.make(Path(path))
    debugger.dump_normalized_yamldict()
