
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
root.title("Tkinter ウィジェット例（タブ分割 + grid配置）")
root.geometry("480x320")

# ====== Notebook（タブ） ======
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

tab_input = ttk.Frame(notebook, padding=12)
tab_settings = ttk.Frame(notebook, padding=12)
tab_actions = ttk.Frame(notebook, padding=12)

notebook.add(tab_input, text="入力")
notebook.add(tab_settings, text="設定")
notebook.add(tab_actions, text="操作")

# ====== タブ1：入力 ======
ttk.Label(tab_input, text="名前").grid(row=0, column=0, padx=6, pady=6, sticky="w")
entry_name = ttk.Entry(tab_input, width=28)
entry_name.grid(row=0, column=1, padx=6, pady=6, sticky="we")
tab_input.columnconfigure(1, weight=1)  # Entryを横に伸ばす
tab_input.rowconfigure(99, weight=1)    # 下に余白

# ====== タブ2：設定 ======
# ラジオボタン
ttk.Label(tab_settings, text="モード").grid(row=0, column=0, padx=6, pady=6, sticky="w")
radio_var = tk.StringVar(value="通常")
modes = ["通常", "高速", "安全"]
for i, m in enumerate(modes):
    ttk.Radiobutton(tab_settings, text=m, value=m, variable=radio_var).grid(
        row=0, column=1+i, padx=4, pady=6, sticky="w"
    )

# チェックボックス
check_var = tk.IntVar(value=0)
ttk.Checkbutton(tab_settings, text="機能を有効化", variable=check_var).grid(
    row=1, column=1, padx=6, pady=6, sticky="w"
)

# コンボボックス
ttk.Label(tab_settings, text="選択").grid(row=2, column=0, padx=6, pady=6, sticky="w")
options = ["A", "B", "C"]
combo_var = tk.StringVar(value=options[0])
combo = ttk.Combobox(tab_settings, textvariable=combo_var, values=options,
                     state="readonly", width=10)
combo.grid(row=2, column=1, padx=6, pady=6, sticky="w")

# 見た目調整
for c in range(0, 5):
    tab_settings.columnconfigure(c, weight=0)
tab_settings.columnconfigure(1, weight=1)
tab_settings.rowconfigure(99, weight=1)

# ====== タブ3：操作 ======
run_btn = ttk.Button(tab_actions, text="実行", command=on_run)
run_btn.grid(row=0, column=0, padx=6, pady=12, sticky="e")

reset_btn = ttk.Button(tab_actions, text="リセット", command=on_reset)
reset_btn.grid(row=0, column=1, padx=6, pady=12, sticky="w")

# 余白と伸縮
tab_actions.columnconfigure(0, weight=1)
tab_actions.columnconfigure(1, weight=1)
tab_actions.rowconfigure(99, weight=1)

# （任意）タブ切り替えイベント
def on_tab_changed(event):
    current = event.widget.select()
    tab_text = event.widget.tab(current, "text")
    # 例：タブに応じてフォーカスを移す
    if tab_text == "入力":
        entry_name.focus_set()
    elif tab_text == "設定":
        combo.focus_set()

notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

root.mainloop()
