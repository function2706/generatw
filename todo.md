# ToDo

era から切り離し, 単一キャラクターとの交流でプロンプトを組み立てる方式へ移行済み.
(旧 Parser/Interpreter/Prompter/era 連携は撤去. 詳細は yamls/character_yaml_spec.md)

## Character (交流エンジン)

- [ ] LLM セリフプロバイダ (`character/dialogue.py` の DialogueProvider 実装を追加)
- [ ] アクション履歴を DialogueContext に持たせて文脈依存のセリフ/生成に活用
- [ ] 時間帯・場所など環境パラメータの追加 (parameters に足すだけで拡張可)
- [ ] サンプル以外の実キャラ YAML を用意

## Displayer

- [ ] パラメータを手動で編集できる UI (デバッグ用)
- [ ] セリフ欄のログ表示 (直近数件を残す)
- [ ] アクションの precondition 未達ボタンをグレーアウト表示

## Generator / Archiver / Master

- 現状維持 (プロンプト供給元が CharacterManager に替わっただけ)
