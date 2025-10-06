import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import math, re

def clamp_coord(x, w): return max(0, min(w - 1, int(x)))
def sign(v): return 1 if v > 0 else (-1 if v < 0 else 0)
def set_pixel(img, x, y, color):
    w, h = img.size
    if 0 <= x < w and 0 <= y < h:
        img.putpixel((x, y), color)

def dda_line(img, x1, y1, x2, y2, color):
    dx, dy = x2 - x1, y2 - y1
    L = max(abs(dx), abs(dy))
    if L == 0: set_pixel(img, round(x1), round(y1), color); return
    dx_step, dy_step = dx / L, dy / L
    x, y = x1, y1
    for _ in range(int(L) + 1):
        set_pixel(img, round(x), round(y), color)
        x += dx_step; y += dy_step

def brez_float_line(img, x1, y1, x2, y2, color):
    sx, sy = sign(x2 - x1), sign(y2 - y1)
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    if dx == 0 and dy == 0: set_pixel(img, round(x1), round(y1), color); return
    if dy > dx: dx, dy, flag = dy, dx, 1
    else: flag = 0
    m = dy / dx
    e = m - 0.5
    x, y = x1, y1
    for _ in range(int(dx) + 1):
        set_pixel(img, int(x), int(y), color)
        if e >= 0:
            if flag: x += sx
            else: y += sy
            e -= 1
        if flag: y += sy
        else: x += sx
        e += m

def brez_int_line(img, x1, y1, x2, y2, color):
    x1, y1, x2, y2 = map(int, [round(x1), round(y1), round(x2), round(y2)])
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    sx, sy = sign(x2 - x1), sign(y2 - y1)
    err = dx - dy
    while True:
        set_pixel(img, x1, y1, color)
        if x1 == x2 and y1 == y2: break
        e2 = 2 * err
        if e2 > -dy: err -= dy; x1 += sx
        if e2 < dx: err += dx; y1 += sy

def builtin_line(img, x1, y1, x2, y2, color):
    draw = ImageDraw.Draw(img)
    draw.line((x1, y1, x2, y2), fill=color)

def foot_of_perpendicular(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    denom = dx*dx + dy*dy
    if denom == 0: return (x1, y1)
    t = ((px-x1)*dx + (py-y1)*dy) / denom
    return (x1 + t*dx, y1 + t*dy)

def save_ppm_ascii(image, path):
    w, h = image.size
    with open(path, "w") as f:
        f.write("P3\n")
        f.write(f"{w} {h}\n255\n")
        for y in range(h):
            row = []
            for x in range(w):
                r, g, b = image.getpixel((x, y))
                row.append(f"{r} {g} {b}")
            f.write(" ".join(row) + "\n")

class App:
    def __init__(self, root):
        self.root = root
        root.title("ЛР3")
        self.W, self.H = 600, 600
        self.img = Image.new("RGB", (self.W, self.H), (255,255,255))
        self.photo = ImageTk.PhotoImage(self.img)

        ctrl = tk.Frame(root); ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        tk.Button(ctrl, text="Открыть SVG", command=self.load_svg).pack(fill="x", pady=2)

        tk.Label(ctrl, text="Алгоритм:").pack(pady=(8,0))
        self.alg_var = tk.StringVar(value="dda")
        for t,v in [("ЦДА (DDA)","dda"),("Брезенхем","brez_f"),
                    ("Брезенхем целочисленный","brez_i"),("Встроенный","builtin")]:
            tk.Radiobutton(ctrl, text=t, variable=self.alg_var, value=v).pack(anchor="w")

        tk.Button(ctrl, text="Нарисовать", command=self.draw_triangle).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Очистить", command=self.clear_canvas).pack(fill="x", pady=2)
        tk.Button(ctrl, text="Сохранить PPM", command=self.save_ppm).pack(fill="x", pady=2)

        self.canvas = tk.Label(root, image=self.photo)
        self.canvas.pack(side=tk.RIGHT, padx=6, pady=6)

        self.vertices = None

    def load_svg(self):
        path = filedialog.askopenfilename(filetypes=[("SVG files","*.svg")])
        if not path: return
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        m = re.search(r'points="([\d ,.-]+)"', text)
        if not m:
            messagebox.showerror("Ошибка", "Не найден <polygon points=...>")
            return
        nums = list(map(float, re.findall(r'[-]?\d+\.?\d*', m.group(1))))
        if len(nums) < 6:
            messagebox.showerror("Ошибка", "Недостаточно координат")
            return
        self.vertices = nums[:6]
        messagebox.showinfo("SVG", f"Загружены вершины: {self.vertices}")

    def draw_triangle(self):
        if not self.vertices:
            messagebox.showerror("Ошибка", "Сначала загрузите SVG")
            return
        self.img = Image.new("RGB", (self.W, self.H), (255,255,255))
        alg = self.alg_var.get()
        if alg=="dda": func = dda_line
        elif alg=="brez_f": func = brez_float_line
        elif alg=="brez_i": func = brez_int_line
        else: func = builtin_line

        x1,y1,x2,y2,x3,y3 = self.vertices
        blue, red, green = (0,0,200), (200,0,0), (0,150,0)

        func(self.img,x1,y1,x2,y2,blue)
        func(self.img,x2,y2,x3,y3,blue)
        func(self.img,x3,y3,x1,y1,blue)

        for (vx,vy),(ax,ay),(bx,by) in [((x1,y1),(x2,y2),(x3,y3)),
                                        ((x2,y2),(x3,y3),(x1,y1)),
                                        ((x3,y3),(x1,y1),(x2,y2))]:
            fx, fy = foot_of_perpendicular(vx,vy,ax,ay,bx,by)
            func(self.img,vx,vy,fx,fy,red)
            set_pixel(self.img, int(fx), int(fy), green)

        self.update_canvas()

    def clear_canvas(self):
        self.img = Image.new("RGB", (self.W, self.H), (255,255,255))
        self.update_canvas()

    def update_canvas(self):
        self.photo = ImageTk.PhotoImage(self.img)
        self.canvas.configure(image=self.photo)
        self.canvas.image = self.photo

    def save_ppm(self):
        path = filedialog.asksaveasfilename(defaultextension=".ppm",
                                            filetypes=[("PPM ASCII","*.ppm")])
        if not path: return
        save_ppm_ascii(self.img, path)
        messagebox.showinfo("Сохранено", f"PPM файл: {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()