import tkinter as tk
from PIL import Image, ImageTk

def show_image(path):
    root = tk.Tk()
    root.title("画像ビューア")

    # Pillowで画像を開く
    img = Image.open(path)
    tk_img = ImageTk.PhotoImage(img)

    # ラベルに画像を貼り付け
    label = tk.Label(root, image=tk_img)
    label.pack()

    root.mainloop()

if __name__ == "__main__":
    show_image("output.png")
