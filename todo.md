# ToDo

## Archiver

## Displayer

- ログウィンドウ
- 着せ替えモードを拡張タブに追加(指定 yaml の fashion から選べる方式)

## Generaor

## Master

## Parser

- main 画面の upper/lower も fashion_list に記録しておき, ここが変わった = 衣装もリセットとする機構
- 終了時の fashion_list の保存
- Memory をキーカテゴリーごとの dict で管理, Screen ごとに全て記憶し, load するカテゴリーはリスト上に記述(あたらしいリストとして)
- これで sync を基底で定義できる, ただしキーカテゴリーと, 各 Screen でのキーカテゴリーにあたるカテゴリーの設定が必要(key_cat)
- イメージとしては FashionSet を汎用的にする感じ, キーカテゴリーは Interpreter 自身がもち, 各 Screen でキーカテゴリーにあたるカテゴリーを指定する(local_key_cat)
- fashion screen や action のようにキーカテゴリーを他から持ってくる場合は別定義を行う(outsrc_key_cat)
- キーカテゴリーは唯一のカテゴリーパスをもつ(key_cat のもの)
