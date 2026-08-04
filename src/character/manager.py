"""
キャラクターマネージャ

キャラクター YAML の探索・ロード, 現在エンジンの管理, および Master への窓口.
旧 Parser の役割 (現在プロンプトの供給) を置き換える.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from character.engine import ActionResult, CharacterEngine
from character.models import ActionSet, CharacterSheet, PersonaSet
from character.state import CharacterState
from common.functions import dirname_by_prompts


@dataclass(frozen=True)
class CharacterPaths:
    """関連ファイルパス"""

    yaml_dir: Path = Path("yamls")
    characters_dir: Path = Path("yamls/characters")
    actions_yaml: Path = Path("yamls/actions.yaml")
    personas_yaml: Path = Path("yamls/personas.yaml")


@dataclass
class CharacterMeta:
    """キャラ選択 UI 用の軽量メタ情報"""

    char_id: str
    display_name: str
    path: Path


class CharacterManager:
    """
    キャラクターの探索・ロードと現在プロンプトの供給を担う
    """

    def __init__(self, load_state_start: bool = True):
        """
        コンストラクタ

        Args:
            load_state_start (bool): キャラ選択時に保存状態を自動復元するか
        """
        self.paths = CharacterPaths()
        self.load_state_start = load_state_start

        self.actions: ActionSet = self._load_actions()
        self.personas: PersonaSet = self._load_personas()
        self.engine: CharacterEngine | None = None
        self._metas: list[CharacterMeta] = []
        self.refresh_character_list()

    # ------------------------------------------------------------------ #
    # 探索 / ロード
    # ------------------------------------------------------------------ #
    def _load_actions(self) -> ActionSet:
        if self.paths.actions_yaml.exists():
            return ActionSet.load(self.paths.actions_yaml)
        return ActionSet()

    def _load_personas(self) -> PersonaSet:
        if self.paths.personas_yaml.exists():
            return PersonaSet.load(self.paths.personas_yaml)
        return PersonaSet()

    def refresh_character_list(self) -> list[CharacterMeta]:
        """
        キャラクターディレクトリを走査してメタ情報を更新する

        Returns:
            list[CharacterMeta]: メタ情報 (char_id 昇順)
        """
        metas: list[CharacterMeta] = []
        if self.paths.characters_dir.exists():
            for path in sorted(self.paths.characters_dir.glob("*.yaml")):
                try:
                    sheet = CharacterSheet.load(path)
                except Exception as e:  # 壊れた YAML は一覧から除外
                    print(f"Failed to load character '{path.name}': {e}")
                    continue
                metas.append(
                    CharacterMeta(
                        char_id=sheet.char_id, display_name=sheet.display_name, path=path
                    )
                )
        self._metas = metas
        return metas

    @property
    def metas(self) -> list[CharacterMeta]:
        return self._metas

    def _meta_of(self, char_id: str) -> CharacterMeta | None:
        return next((m for m in self._metas if m.char_id == char_id), None)

    def select_character(self, char_id: str) -> bool:
        """
        キャラクターを選択してエンジンを構築する\n
        load_state_start が真なら保存状態を復元, なければ初期状態

        Args:
            char_id (str): キャラ ID

        Returns:
            bool: 成否
        """
        meta = self._meta_of(char_id)
        if meta is None:
            return False

        sheet = CharacterSheet.load(meta.path)
        state = None
        if self.load_state_start:
            state = CharacterState.load(sheet)
        if state is None:
            state = CharacterState.initial(sheet)

        self.engine = CharacterEngine(
            sheet=sheet,
            actions=self.actions,
            state=state,
            persona=self.personas.get(sheet.persona),
        )
        self.engine.refresh_prompt()
        return True

    def reload_current(self) -> bool:
        """
        現在キャラのシートとアクションを再読み込みする (状態は保持し整合を取る)

        Returns:
            bool: 成否 (未選択なら False)
        """
        if self.engine is None:
            return False

        self.actions = self._load_actions()
        self.personas = self._load_personas()
        self.refresh_character_list()

        meta = self._meta_of(self.engine.sheet.char_id)
        if meta is None:
            return False

        sheet = CharacterSheet.load(meta.path)
        state = self.engine.state
        state.reconcile(sheet)
        self.engine = CharacterEngine(
            sheet=sheet,
            actions=self.actions,
            state=state,
            persona=self.personas.get(sheet.persona),
        )
        self.engine.refresh_prompt()
        return True

    # ------------------------------------------------------------------ #
    # アクション / 状態
    # ------------------------------------------------------------------ #
    def apply_action(self, action_id: str, wardrobe_key: str | None = None) -> ActionResult | None:
        """
        現在エンジンでアクションを適用する

        Args:
            action_id (str): アクション ID
            wardrobe_key (str | None): 着せ替え先の衣装キー

        Returns:
            ActionResult | None: 結果 (未選択/未知アクションなら None)
        """
        if self.engine is None:
            return None
        return self.engine.apply_action(action_id, wardrobe_key=wardrobe_key)

    def save_state(self) -> None:
        """現在状態を保存する"""
        if self.engine is not None:
            self.engine.state.save()

    def load_state(self) -> bool:
        """
        保存状態を復元する

        Returns:
            bool: 復元したか (保存がなければ False)
        """
        if self.engine is None:
            return False
        loaded = CharacterState.load(self.engine.sheet)
        if loaded is None:
            return False
        self.engine.state = loaded
        self.engine.refresh_prompt()
        return True

    def reset_state(self) -> None:
        """状態を初期値へ戻す"""
        if self.engine is not None:
            self.engine.reset_state()

    # ------------------------------------------------------------------ #
    # 参照 (Master / Displayer 向け)
    # ------------------------------------------------------------------ #
    @property
    def is_ready(self) -> bool:
        """生成可能なプロンプトを供給できる状態か"""
        return self.engine is not None and bool(self.engine.last_strs[0] or self.engine.last_strs[1])

    @property
    def crnt_strs(self) -> tuple[str, str] | None:
        """現在の (positive, negative) 文字列 (未選択なら None)"""
        if self.engine is None:
            return None
        return self.engine.last_strs

    @property
    def crnt_prompt_dir(self) -> str | None:
        """現在プロンプトに紐づくディレクトリ名 (md5)"""
        strs = self.crnt_strs
        return dirname_by_prompts(strs[0], strs[1]) if strs is not None else None

    @property
    def sheet(self) -> CharacterSheet | None:
        return self.engine.sheet if self.engine is not None else None

    @property
    def state(self) -> CharacterState | None:
        return self.engine.state if self.engine is not None else None

    @property
    def char_id(self) -> str | None:
        return self.engine.sheet.char_id if self.engine is not None else None
