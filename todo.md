・TW：出かけた場合の場所取得
・画像ファイルの格納構造を規定(画像とメタデータをどう紐づける？)
　→そもそもメタデータを取り出せるようにしないといけない(yiのCopilotのログ参照)
・同じメタデータを持つ画像群を行き来できるボタンを追加("<"と">")
・生成済みのメタデータに紐づく画像をランダムで表示する機構を追加
・画像群の更新仕様を規定, 新しい画像はいつ追加するか？またはボタン押下のみをトリガとするか？
・アップスケールデーモンを追加, アップスケールは時間がかかるので生成後にアトミックに行うのではなく, GUIに表示されていない段階で裏で逐次実施するようにする


import io, base64, json
from PIL import Image, PngImagePlugin
import requests

response = requests.post(
    f"http://{self.sd_configs.ipaddr}:{self.sd_configs.port}/sdapi/v1/txt2img",
    json=json, timeout=self.pm_configs.timeout_sec
)
response.raise_for_status()
body = response.json()

images = body.get("images")
if not images:
    print("API response without images.")
    return ""

# 画像データ（先頭の data:image/png;base64, が付く場合はsplitで除去）
image_b64 = images[0].split(",", 1)[-1]
image = Image.open(io.BytesIO(base64.b64decode(image_b64)))

# --- メタ情報の取得（1）: 直接レスポンスのinfoから取り出す ---
# A1111のinfoはJSON文字列になっており、その中に"infotexts"配列があることが多い
# 例: json.loads(body["info"])["infotexts"][0]
pnginfo_text = None
try:
    infoobj = json.loads(body.get("info", "{}"))
    infotexts = infoobj.get("infotexts")
    if isinstance(infotexts, list) and infotexts:
        pnginfo_text = infotexts[0]
except Exception:
    pass

# --- メタ情報の取得（2）: /sdapi/v1/png-info に画像を渡してサーバー側で整形してもらう ---
# こちらの方が安定してパラメータ文字列（PNG Info相当）が得られます。
if not pnginfo_text:
    payload2 = {"image": "data:image/png;base64," + image_b64}
    response2 = requests.post(
        f"http://{self.sd_configs.ipaddr}:{self.sd_configs.port}/sdapi/v1/png-info",
        json=payload2, timeout=self.pm_configs.timeout_sec
    )
    response2.raise_for_status()
    pnginfo_text = response2.json().get("info", "")

# PNGのtEXtチャンクに埋め込んで保存（WebUIのPNG Infoで復元可能）
meta = PngImagePlugin.PngInfo()
# キーは "parameters" が慣例（A1111のPNG Infoタブが読む）
meta.add_text("parameters", pnginfo_text)

image_path = self.gen_image_path()
image.save(image_path, pnginfo=meta)




    def embed_metainfo(self, info_obj: Any) -> None:
        pnginfo_text = None
        try:
            infotexts = info_obj.get("infotexts", [])
            if isinstance(infotexts, list) and infotexts:
                pnginfo_text = infotexts[0]
        except Exception:
            pass