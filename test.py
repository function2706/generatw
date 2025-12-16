
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

def on_run():
    # 入力値の取得
    name = entry_name.get()
    mode = radio_var.get()
    enable_feature = check_var.get()  # 1 or 0
    choice = combo_var.get()

    msg = (
        f"名前: {name}\n"
        f"モード: {mode}\n"
        f"機能有効: {bool(enable_feature)}\n"
        f"選択: {choice}"
    )
    messagebox.showinfo("実行結果", msg)

def on_reset():
    entry_name.delete(0, tk.END)
    radio_var.set("通常")
    check_var.set(0)
    combo_var.set(options[0])

root = tk.Tk()
root.title("Tkinter ウィジェット例（grid配置）")
root.geometry("420x280")

# ====== フレームでまとまりを作る（任意） ======
frm = ttk.Frame(root, padding=12)
frm.grid(row=0, column=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# ====== ラベル + テキストボックス（Entry） ======
ttk.Label(frm, text="名前").grid(row=0, column=0, padx=6, pady=6, sticky="w")
entry_name = ttk.Entry(frm, width=28)
entry_name.grid(row=0, column=1, padx=6, pady=6, sticky="we")
frm.columnconfigure(1, weight=1)  # Entryを横に伸ばす

# ====== ラジオボタン（Radiobutton） ======
ttk.Label(frm, text="モード").grid(row=1, column=0, padx=6, pady=6, sticky="w")
radio_var = tk.StringVar(value="通常")
modes = ["通常", "高速", "安全"]
for i, m in enumerate(modes):
    ttk.Radiobutton(frm, text=m, value=m, variable=radio_var).grid(
        row=1, column=1+i, padx=4, pady=6, sticky="w"
    )

# ====== チェックボックス（Checkbutton） ======
check_var = tk.IntVar(value=0)
ttk.Checkbutton(frm, text="機能を有効化", variable=check_var).grid(
    row=2, column=1, padx=6, pady=6, sticky="w"
)

# ====== プルダウン（Combobox / OptionMenu） ======
ttk.Label(frm, text="選択").grid(row=3, column=0, padx=6, pady=6, sticky="w")

# Combobox（ttk推奨。入力可否は state で制御）
options = ["A", "B", "C"]
combo_var = tk.StringVar(value=options[0])
combo = ttk.Combobox(frm, textvariable=combo_var, values=options, state="readonly", width=10)
combo.grid(row=3, column=1, padx=6, pady=6, sticky="w")

# OptionMenu を使いたい場合（参考）
# option_var = tk.StringVar(value=options[0])
# opt = ttk.OptionMenu(frm, option_var, options[0], *options)
# opt.grid(row=3, column=2, padx=6, pady=6, sticky="w")

# ====== 実行ボタン・リセットボタン ======
run_btn = ttk.Button(frm, text="実行", command=on_run)
run_btn.grid(row=4, column=1, padx=6, pady=12, sticky="e")

reset_btn = ttk.Button(frm, text="リセット", command=on_reset)
reset_btn.grid(row=4, column=2, padx=6, pady=12, sticky="w")

# ====== 余白と伸縮（見た目調整） ======
for c in range(0, 4):
    frm.columnconfigure(c, weight=0)
frm.columnconfigure(1, weight=1)   # 入力欄やボタン行を少し伸縮
frm.rowconfigure(99, weight=1)     # 下方向に余白

root.mainloop()
