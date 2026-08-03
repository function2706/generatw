"""
キャラクターの実行時状態と JSON 永続化

内部パラメータの現在値と現在の衣装を保持する.
セーブ先は ``memories/<char_id>.state.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from character.models import CharacterSheet
from common.functions import PathConsts


@dataclass
class CharacterState:
    """
    キャラクターの実行時状態

    Attributes:
        char_id (str): キャラ ID
        params (dict[str, object]): パラメータ ID -> 現在値
        outfit (str): 現在の衣装キー
    """

    char_id: str
    params: dict[str, object] = field(default_factory=dict)
    outfit: str = ""

    @classmethod
    def initial(cls, sheet: CharacterSheet) -> CharacterState:
        """
        シートの初期値から初期状態を作る

        Args:
            sheet (CharacterSheet): キャラシート

        Returns:
            CharacterState: 初期状態
        """
        return cls(
            char_id=sheet.char_id,
            params={name: pdef.init for name, pdef in sheet.parameters.items()},
            outfit=sheet.init_outfit,
        )

    def reconcile(self, sheet: CharacterSheet) -> None:
        """
        シート定義との整合を取る (パラメータの増減・衣装削除に追従)\n
        - 未知パラメータを除去, 欠落パラメータを init で補填, 値を clamp\n
        - 衣装が存在しない場合は初期衣装へ

        Args:
            sheet (CharacterSheet): キャラシート
        """
        new_params: dict[str, object] = {}
        for name, pdef in sheet.parameters.items():
            new_params[name] = pdef.clamp(self.params.get(name, pdef.init))
        self.params = new_params

        if self.outfit not in sheet.wardrobe:
            self.outfit = sheet.init_outfit

    @staticmethod
    def _path(char_id: str) -> Path:
        return PathConsts.mem_dir / f"{char_id}.state.json"

    def save(self) -> None:
        """状態を JSON へ保存する"""
        PathConsts.mem_dir.mkdir(parents=True, exist_ok=True)
        with open(self._path(self.char_id), "w", encoding="utf-8") as f:
            json.dump(
                {"char_id": self.char_id, "params": self.params, "outfit": self.outfit},
                f,
                ensure_ascii=False,
                indent=2,
            )

    @classmethod
    def load(cls, sheet: CharacterSheet) -> CharacterState | None:
        """
        保存済み状態を読み込み, シートと整合させて返す\n
        保存ファイルがない場合は None

        Args:
            sheet (CharacterSheet): キャラシート

        Returns:
            CharacterState | None: 状態 (なければ None)
        """
        path = cls._path(sheet.char_id)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        state = cls(
            char_id=sheet.char_id,
            params=dict(d.get("params") or {}),
            outfit=str(d.get("outfit") or sheet.init_outfit),
        )
        state.reconcile(sheet)
        return state
