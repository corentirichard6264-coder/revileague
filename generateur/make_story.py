"""Stories Instagram de Léo (1080x1920 JPEG).

Usage : python3 make_story.py spec.json sortie.jpg
  question : {"type": "question", "question": "Quelle est la planète\\nla plus proche\\ndu Soleil ?",
              "options": ["Vénus", "Mercure", "Mars"], "badge": "6e • SVT"}
  reponse  : {"type": "reponse", "question": "La planète la plus\\nproche du Soleil ?", "reponse": "Mercure",
              "explication": "Elle tourne à environ\\n58 millions de km\\ndu Soleil"}
Pas d'emoji (la police ne les a pas). Lignes courtes : \\n pour couper (≤ 22 caractères par ligne de question).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
NAVY, GOLD, WHITE, GREEN, GREY = (31, 42, 68), (233, 190, 60), (255, 255, 255), (46, 160, 90), (90, 100, 130)
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
font = lambda bold, n: ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf" if bold else "Poppins-Medium.ttf"), n)

spec, out = json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]
img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)
for y in range(H):  # dégradé bleu nuit
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(20 + 25 * t), int(28 + 40 * t), int(60 + 70 * t)))
for x, y, r in [(120, 180, 3), (900, 260, 4), (980, 900, 3), (60, 1300, 4), (820, 1500, 3), (300, 1800, 3), (700, 120, 2)]:
    d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 210, 255))  # quelques étoiles discrètes


def center(y, text, f, fill):
    d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def fit(lines, maxw, size):  # réduit la taille jusqu'à ce que chaque ligne tienne
    while size > 40 and max(d.textlength(l, font=font(True, size)) for l in lines) > maxw:
        size -= 4
    return size


titre = "QUESTION DU JOUR" if spec["type"] == "question" else "LA RÉPONSE !"
d.rounded_rectangle([90, 260, 990, 380], 60, fill=GOLD if spec["type"] == "reponse" else NAVY)
center(278, titre, font(True, 64), NAVY if spec["type"] == "reponse" else GOLD)
if spec.get("badge"):
    center(410, spec["badge"], font(False, 44), WHITE)

lines = spec["question"].split("\n")
size = fit(lines, 820, 84)
top = 520
box_h = 120 + len(lines) * int(size * 1.5) + (110 if spec["type"] == "question" else 0)
d.rounded_rectangle([70, top, 1010, top + box_h], 50, fill=WHITE, outline=NAVY, width=8)
for i, l in enumerate(lines):
    center(top + 60 + i * int(size * 1.5), l, font(True, size), NAVY)
y = top + box_h + 90

if spec["type"] == "question":
    center(top + box_h - 120, "  •  ".join(spec["options"]), font(False, 54), GREY)
    center(y, "Réponse demain en story !", font(True, 66), WHITE)
    center(y + 100, "Garde ta réponse en tête...", font(False, 46), WHITE)
else:
    d.rounded_rectangle([140, y, 940, y + 150], 75, fill=GREEN)
    center(y + 30, spec["reponse"], font(True, fit([spec["reponse"]], 740, 80)), WHITE)
    for i, l in enumerate(spec.get("explication", "").split("\n")):
        center(y + 210 + i * 70, l, font(False, 50), WHITE)

d.rounded_rectangle([250, 1660, 830, 1780], 60, fill=GOLD)
center(1682, "— Léo de RéviLeague", font(True, 50), NAVY)
img.save(out, quality=92)
print("OK", out)
