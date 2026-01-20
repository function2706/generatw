・img2imgタスクの実装
・Good→アップスケール候補にキューイングに変更
　→TaskBlueprintをtxt2imgとimg2imgに派生させる
　→優先度は常にtxt2img, キューは一つだがimg2imgは常にtxt2imgのあとにスタックされる
　→txt2imgタスク、img2imgタスクのみリセットのボタン、全てリセットのボタン
・Bad→削除ボタンに変更、押下の瞬間にこれに関するタスクを削除
・クリップボードパース失敗時のログ(パースできなかった文字列と正規表現のペアで残しておく)
・生成条件の精査
　→最大数の設定？最大数に近づくほど確率を減らすモード(チェックボックス)
　→最大数設定テキストボックス
・表示中画像情報ウィンドウ(画像というかディレクトリ？+サイズなどの画像自体の情報)
・displayer内でしているpostをTaskmanagerに逃がす(そうしないと通信できない場合にtimeoutまでGUIが固まる)
　→progressタスクもつくり、txt2imgと同じキューに積み、優先度はprogressがtxt/img2imgより強いとする
　→その結果はTaskManagerのメンバに常に最新を保存し、Displayerがedgepointでこれを見てバーを更新
　→interruptも最優先タスクとする、つまり基本的にポスト処理はタスクキューに積んでからスレッド内で実施
・タスク情報のTreeView化
　→タスクの種類も記載
　→タスクごとに記載する情報はどうする？すべて書いておく？
・ComfyUI対応
　→起動時の選択画面でIN=era種類の他にOUT=A1111/ComfyUIを選べるように
　→TaskManagerをA1111ManagerとComfyUIManagerに継承
・構造の刷新、eraから吸い出すクラス(Sniffer)を独立
　　→[era]->[Sniffer]->[Master]┬>[TaskManager]->[Server]
　　　　　　　　　　　　　　　　　└>[PicManager]->[Displayer]
　→Masterと他のモジュールとの間の通信を行うイベント定義ファイルを作成する
　→キューの種類はModuleX->Master->ModuleYのためのrequest, ModuleX->Master(状態報告)のためのreport
　　これをMasterがもち、各Moduleにはキューのオブジェクトを渡す
　→この過程でdisplayer内でしているpostも逃がせる
　→tk.rootはMasterがもつ、afterもMasterが呼び出す、tkinterアプリのメインはtkinterループらしい(by ChatGPT)
・Generatorを派生させた際にDisplayerの情報ウィンドウのタイトルバー文字列に追加