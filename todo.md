・TW：出かけた場合の場所取得
・生成済みのメタデータに紐づく画像をランダムで表示する機構を追加
→TWは能力表示画面経由でない場合に表示とすべきか？プロンプト決定ロジックとの整合性を考えないといけない
　モードごとにランダム表示と生成を判断する関数を実装する必要がありそう
・画像群の更新仕様を規定, 新しい画像はいつ追加するか？またはボタン押下のみをトリガとするか？
・アップスケールデーモンを追加, アップスケールは時間がかかるので生成後にアトミックに行うのではなく, GUIに表示されていない段階で裏で逐次実施するようにする
→Good / Bad ボタンを追加, Good を押すとアップスケール対象にキュー, Badは削除対象 or 即時削除
削除対象になると最大数超過時に優先的に削除していくとか
・ディレクトリ監視スレッドを立てて, 外部からの削除や変更に対応
→変更の場合はどうする？変更があった場合はメタデータ汚染の可能性もあるので消す？
crntのpicが消されたり変更されたりした場合は他の画像にランダムで移動？
・GUIクラス作成
・メタデータ埋め込みをPicInfoコンストラクタに統合(image: Imageとinfo_obj: Anyの引数指定でどちらの初期化を行うかを分岐させる)
・gen_picを純粋に生成する関数へ、saveと分離
・worker内、生成すべきでない条件に生成中を統合、失敗時は既存のファイルを表示？
        """
        画像生成スレッドエントリポイント\n
        生成から表示までを実施する(複数個生成した場合はランダムで 1 つ表示)\n
        生成すべきでない(SD 生成中を含む)と判断した場合はすでに生成した画像を表示する\n
        """
        def worker():
            crnt_pic_paths = self.get_pic_list()

            # 生成すべき or 画像が無いなら生成する
            is_generatable = (
                self.should_gen_pic() and not self.flags.is_generating
            ) or not crnt_pic_paths
            new_pic_paths = self.gen_pic() if is_generatable else []

            # 生成が必要だったのに失敗した場合は中断
            if is_generatable and not new_pic_paths:
                return

            self.update_image(PicStats(random.choice(crnt_pic_paths + new_pic_paths)))
・PicManagerはリストをList[Dict[str, List[PicStats]]]として持つべき(ディレクトリ名をPath→str)
・生成した場合, 記録中ステータスが生成画像のディレクトリ名と一致しない(=プロンプト不一致)場合は表示しないようにすべきか
→というより表示は常に記録中ステータスのものしかできないようにすべき