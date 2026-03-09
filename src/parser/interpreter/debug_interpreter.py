"""
デバッグ用 Interpreter
"""

from __future__ import annotations

from pathlib import Path

from parser.interpreter.interpreter import Interpreter, ScreenConfig, ScreenTable


class DebugInterpreter(Interpreter):
    """
    デバッグ用 Interpreter
    """

    def __init__(self, yamlpath: Path):
        super().__init__(yamlpath)

    @property
    def screen_table(self) -> ScreenTable:
        return {
            "main": ScreenConfig.set(
                primitive_enhanced_category=[
                    (("character", "name"), None, False),
                    (("character", "vibe"), None, False),
                    (("character", "upper"), None, False),
                    (("character", "lower"), None, False),
                ],
                essential_condition=None,
                syncer=None,
            )
        }

    def save_state(self) -> dict:
        """
        このインスタンスの状態を保存可能な形式で返す\n
        DebugInterpreter は記憶を持たない

        Returns:
            dict: 常に空の辞書
        """
        return {}

    def restore_state(self, state: dict) -> None:
        """
        指定の状態から記憶を復元する\n
        DebugInterpreter は記憶がないため何もしない

        Args:
            state (dict): 保存された状態 (無視される)
        """
        return
