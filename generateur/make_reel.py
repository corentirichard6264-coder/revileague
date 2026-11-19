"""Générateur de réels RéviLeague (1080x1920, 30 fps, son synthétique).

Usage : python3 make_reel.py spec.json sortie.mp4

Trois formats de spec JSON :
  quiz   : {"type":"quiz","badge":"4e • MATHS","hook":"Tu peux répondre\\nen 5 secondes ?",
            "question":"2³ × 2² = ?","options":["10","32","64","12"],"answer":1,
            "explain":"On additionne les exposants :\\n3 + 2 = 5, donc 2 puissance 5 = 32",
            "xp":50,"countdown":5}
  serie  : {"type":"serie","badge":"COLLÈGE • MIX","hook":"5 questions.\\nTu fais combien ?","countdown":5,"xp":250,
            "questions":[{"badge":"4e • MATHS","question":...,"options":[...],"answer":1,"explain":...}, ...]}
           Vidéo d'au moins 61 s (le script refuse sinon). 3 options par question conseillées, "image_query" (anglais)
           ou "image" (URL) par question pour l'illustration (Openverse, domaine public / CC0).
           Voix off Fish Audio si la variable d'environnement FISH_API_KEY existe (FISH_VOICE_ID = voix choisie) :
           elle lit l'intro, chaque question + ses 4 réponses, la correction, le score et la fin ; le chrono
           démarre après la lecture. Par question, "dit_question" / "dit_explication" (optionnels) remplacent
           le texte lu quand l'écrit se lit mal (ex. "2³ × 2²" -> "2 puissance 3 fois 2 puissance 2").
  astuce : {"type":"astuce","badge":"COLLÈGE • MIX","hook":"5 infos à connaître\\navant le contrôle","xp":100,
            "infos":[{"badge":"3e • FRANÇAIS","title":"Participe passé\\navec avoir",
                      "lines":["S'accorde avec le COD...","...seulement s'il est placé AVANT"],
                      "example":"Les pommes que j'ai mangées"}, ...]}
           Vidéo d'au moins 60 s (le script refuse sinon) : 4 à 6 infos. Voix off (intro, chaque info, fin) ;
           "dit" (optionnel) par info remplace le texte lu (titre + lignes + « Exemple : ... »).
Tous les formats ont une musique de fond originale synthétisée (libre de droits), baissée sous la voix off.
Les 0,5 premières secondes sont une couverture (titre du format, accroche, XP) : Instagram et TikTok prennent
la 1re image comme miniature. Elle est aussi enregistrée à côté de la vidéo (<nom>-cover.jpg).
"cover_title" (optionnel) remplace le titre de la couverture (QUIZ / LE SAVAIS-TU ? / DÉFI DE LA LIGUE).
Le script refuse un texte contenant un caractère absent de la police (ex. ⁵, ᵉ, →).
"""
import json, math, os, struct, subprocess, sys, wave
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
FD = "/usr/share/fonts/truetype/google-fonts/"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_cache = {}
def F(style, size):
    k = (style, size)
    if k not in _cache:
        local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", f"Poppins-{style}.ttf")
        p = local if os.path.exists(local) else FD + f"Poppins-{style}.ttf"
        _cache[k] = ImageFont.truetype(p if os.path.exists(p) else FALLBACK, size)
    return _cache[k]

NAVY = (15, 20, 32); NAVY2 = (28, 36, 60); CARD = (34, 44, 72)
GOLD = (255, 196, 61); CYAN = (64, 214, 255); GREEN = (52, 211, 120)
RED = (255, 92, 108); WHITE = (245, 247, 255); GREY = (150, 160, 190)

def check_glyphs(spec):
    try:
        from fontTools.ttLib import TTFont
        cmap = TTFont(F("Bold", 10).path).getBestCmap()
    except Exception:
        return
    txt = json.dumps(spec, ensure_ascii=False)
    bad = sorted({c for c in txt if ord(c) > 127 and ord(c) not in cmap})
    if bad:
        sys.exit("Caractères non supportés par la police, à réécrire : " + " ".join(bad))

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def prog(t, a, d): return ease((t - a) / d)
def back(t, a, d):
    """Entrée avec rebond (dépasse un peu puis revient) : 0 -> 1."""
    x = max(0.0, min(1.0, (t - a) / d)) - 1; return 1 + 2.7 * x ** 3 + 1.7 * x ** 2

# couleur de fond par matière (lue dans le badge, ex. « 4e • MATHS »)
SUBJECTS = [("MATH", (40, 95, 215)), ("FRAN", (185, 50, 110)), ("HIST", (190, 110, 30)), ("GÉO", (190, 110, 30)),
            ("SVT", (30, 150, 85)), ("PHYS", (125, 60, 200)), ("CHIM", (125, 60, 200)), ("ANGL", (200, 55, 55)),
            ("PHILO", (40, 140, 160))]
_bgs = {}
def bg_for(badge):
    tint = next((c for k, c in SUBJECTS if k in badge.upper()), (40, 60, 120))
    if tint not in _bgs: _bgs[tint] = make_bg(tint)
    return _bgs[tint], tint

def deco(im, t, tint):
    """Formes qui flottent lentement vers le haut, couleur de la matière (fond vivant)."""
    def d(dr):
        for i in range(16):
            x = (i * 389 + 70) % W + 30 * math.sin(t * 0.8 + i)
            y = H + 150 - ((t * (40 + 25 * (i % 3)) + i * 260) % (H + 300))
            s = 18 + (i % 4) * 10; c = tuple(min(255, v + 90) for v in tint) + (55,)
            if i % 3 == 0: dr.ellipse([x - s, y - s, x + s, y + s], outline=c, width=6)
            elif i % 3 == 1: dr.rectangle([x - s, y - 4, x + s, y + 4], fill=c); dr.rectangle([x - 4, y - s, x + 4, y + s], fill=c)
            else: dr.polygon([(x, y - s), (x + s, y + s * 0.8), (x - s, y + s * 0.8)], outline=c, width=6)
    im.alpha_composite(layer(d, 1))

def confetti(im, u, cx, cy, seed):
    """Explosion de confettis depuis (cx, cy), u = temps depuis la révélation (1,3 s)."""
    if not 0 <= u < 1.3: return
    import random
    rnd = random.Random(seed); cols = [GOLD, CYAN, GREEN, RED, WHITE]
    def d(dr):
        for _ in range(46):
            a = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(500, 1300); c = rnd.choice(cols); s = rnd.uniform(9, 17)
            x = cx + math.cos(a) * v * u; y = cy + math.sin(a) * v * u - 300 * u + 1400 * u * u
            dr.rectangle([x - s, y - s / 2, x + s, y + s / 2], fill=c + (255,))
    im.alpha_composite(layer(d, 1 - prog(u, 0.8, 0.5)))

def shake(im, u):
    """Petit tremblement de l'écran pendant 0,35 s après u = 0."""
    if not 0 <= u < 0.35: return im
    k = 1 - u / 0.35
    return ImageChops.offset(im, int(16 * k * math.sin(u * 90)), int(10 * k * math.cos(u * 70)))

def make_bg(tint=(40, 60, 120)):
    bg = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * k) for i in range(3)))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([-300, -200, 800, 800], fill=tint); gd.ellipse([400, 1200, 1500, 2300], fill=tuple(int(v * 0.8) for v in tint))
    bg = Image.blend(bg, ImageChops.lighter(bg, glow.filter(ImageFilter.GaussianBlur(180))), 0.85)
    gd = ImageDraw.Draw(bg)
    for x in range(0, W, 90):
        for y in range(0, H, 90):
            gd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(38, 48, 78))
    return bg

def ctext(dr, y, txt, font, fill, spacing=10):
    bb = dr.multiline_textbbox((0, 0), txt, font=font, spacing=spacing, align="center")
    dr.multiline_text(((W - (bb[2] - bb[0])) / 2, y), txt, font=font, fill=fill, spacing=spacing, align="center")

def fit(txt, style, size, maxw):
    """Réduit la taille jusqu'à ce que chaque ligne tienne dans maxw."""
    while size > 28 and max(F(style, size).getlength(l) for l in txt.split("\n")) > maxw:
        size -= 4
    return F(style, size)

def layer(fn, a):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(L))
    if a < 1: L.putalpha(L.getchannel("A").point(lambda v: int(v * max(0, a))))
    return L

def header(im, badge):
    def h(dr):
        dr.rounded_rectangle([60, 70, 520, 160], 45, fill=(255, 255, 255, 18))
        dr.text((95, 88), "Révi", font=F("Bold", 50), fill=WHITE)
        dr.text((95 + F("Bold", 50).getlength("Révi"), 88), "League", font=F("Bold", 50), fill=GOLD)
        f = F("Bold", 38); bw = f.getlength(badge) + 60
        dr.rounded_rectangle([W - 60 - bw, 82, W - 60, 148], 33, fill=CYAN + (255,))
        dr.text((W - 60 - bw + 30, 90), badge, font=f, fill=NAVY)
    im.alpha_composite(layer(h, 1))

def xp_block(im, t, t0, t_end, xp, y=1665):
    p = prog(t, t0, 0.35); a = p * (1 - prog(t, t_end - 0.4, 0.4))
    def x(dr):
        ctext(dr, y + 40 * (1 - p), f"+{xp} XP", F("Bold", 120), GOLD + (255,))
        bx0, bx1, by = 190, W - 190, y + 180
        dr.rounded_rectangle([bx0, by - 18, bx1, by + 18], 18, fill=(255, 255, 255, 30))
        dr.rounded_rectangle([bx0, by - 18, bx0 + (bx1 - bx0) * (0.55 + 0.3 * prog(t, t0 + 0.3, 1.2)), by + 18], 18, fill=CYAN + (255,))
    im.alpha_composite(layer(x, a))

def cta(im, t, t0):
    p = prog(t, t0, 0.5)
    def c(dr):
        ctext(dr, 640 + 40 * (1 - p), "Révise comme\ndans un jeu.", F("Bold", 100), WHITE + (255,), 6)
        ctext(dr, 940 + 40 * (1 - p), "XP  •  Rangs  •  Classements\nde la 6e à la Terminale", F("Medium", 50), GREY + (255,), 16)
        bw = 760; x0 = (W - bw) / 2
        dr.rounded_rectangle([x0, 1200, x0 + bw, 1350], 75, fill=GOLD + (255,))
        dr.text((W / 2, 1275), "Rejoins la Ligue", font=F("Bold", 64), fill=NAVY + (255,), anchor="mm")
        ctext(dr, 1400, "Lien en bio", F("Medium", 48), CYAN + (255,))
    im.alpha_composite(layer(c, p))

# ---------------------------------------------------------------- QUESTION (pièces communes quiz / série)
def q_fonts(q):
    return (fit(q["question"], "Bold", 120, W - 260), [fit(o, "Bold", 80, 300) for o in q["options"]],
            fit(q["explain"], "Medium", 52, W - 240))

def draw_question(im, t, q, fonts, cd, T_Q, T_OPT, T_COUNT, T_DIM, T_OUT):
    """Carte question + 4 réponses + compte à rebours + correction, entre T_Q et T_OUT."""
    qf, of, ef = fonts
    T_REVEAL = T_COUNT + cd
    if T_Q <= t < T_OUT:
        a = prog(t, T_Q, 0.25) * (1 - prog(t, T_OUT - 0.4, 0.4))
        sc = 0.8 + 0.2 * back(t, T_Q, 0.5)  # la carte « pop » à l'arrivée
        def qd(dr):
            hw, hh = (W - 180) / 2 * sc, 130 * sc
            dr.rounded_rectangle([W / 2 - hw, 690 - hh, W / 2 + hw, 690 + hh], 40, fill=CARD + (255,), outline=GOLD + (255,), width=5)
            bb = dr.multiline_textbbox((0, 0), q["question"], font=qf, align="center")
            ctext(dr, 690 - (bb[3] - bb[1]) / 2 - bb[1], q["question"], qf, GOLD + (255,))
        im.alpha_composite(layer(qd, a))
    if T_OPT <= t < T_OUT:
        for i, opt in enumerate(q["options"]):
            good = i == q["answer"]
            ap = prog(t, T_OPT + i * 0.12, 0.2) * (1 if good else 1 - prog(t, T_DIM - 0.3, 0.4)) * (1 - prog(t, T_OUT - 0.4, 0.4))
            if ap <= 0: continue
            x0 = 90 + (i % 2) * 470 + (1 if i % 2 else -1) * 160 * (1 - back(t, T_OPT + i * 0.12, 0.45))  # arrivent des côtés
            y0 = 900 + (i // 2) * 230 - (14 * math.sin((t - T_REVEAL) * 14) * (1 - prog(t, T_REVEAL, 0.6)) if good and t >= T_REVEAL else 0)
            fill, outline, dim = CARD, (70, 85, 130), 1
            if t >= T_REVEAL:
                fill, outline, dim = (GREEN, (180, 255, 210), 1) if good else ((60, 40, 55), RED, 0.45)
            def od(dr, x0=x0, y0=y0, fill=fill, outline=outline, opt=opt, i=i, dim=dim):
                dr.rounded_rectangle([x0, y0, x0 + 430, y0 + 190], 36, fill=fill + (int(255 * dim),), outline=outline + (255,), width=5)
                dr.ellipse([x0 + 28, y0 + 55, x0 + 108, y0 + 135], fill=(255, 255, 255, 40))
                dr.text((x0 + 68, y0 + 95), "ABCD"[i], font=F("Bold", 44), fill=WHITE + (255,), anchor="mm")
                dr.text((x0 + 270, y0 + 95), opt, font=of[i], fill=WHITE + (int(255 * max(dim, .6)),), anchor="mm")
            im.alpha_composite(layer(od, ap))
    if T_COUNT <= t < T_REVEAL + 0.3:
        rem = max(0, T_REVEAL - t); frac = rem / cd
        a = prog(t, T_COUNT, 0.3) * (1 - prog(t, T_REVEAL, 0.3))
        def c(dr):
            col = GOLD if rem > 2 else RED
            cx, cy = W // 2, 1490; r = 105 + 16 * prog(rem % 1, 0.75, 0.25)  # pulse à chaque seconde
            dr.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=col + (40,))
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CARD + (255,))
            dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=col + (255,), width=16)
            dr.text((cx, cy), str(math.ceil(rem)), font=F("Bold", int(r)), fill=WHITE + (255,), anchor="mm")
            ctext(dr, 1625, "Mets ta réponse en commentaire", F("Medium", 44), GREY + (255,))
            dr.rounded_rectangle([90, 1720, W - 90, 1744], 12, fill=(255, 255, 255, 30))  # barre qui se vide
            dr.rounded_rectangle([90, 1720, 90 + (W - 180) * frac, 1744], 12, fill=col + (255,))
        im.alpha_composite(layer(c, a))
    if T_REVEAL <= t < T_REVEAL + 0.4:  # flash vert à la révélation
        im.alpha_composite(layer(lambda dr: dr.rectangle([0, 0, W, H], fill=GREEN + (255,)), 0.28 * (1 - prog(t, T_REVEAL, 0.4))))
    gi = q["answer"]
    confetti(im, t - T_REVEAL, 90 + (gi % 2) * 470 + 215, 900 + (gi // 2) * 230 + 95, sum(map(ord, q["question"])))
    if T_REVEAL + 0.3 <= t < T_OUT:
        a = prog(t, T_REVEAL + 0.3, 0.4) * (1 - prog(t, T_OUT - 0.4, 0.4))
        def e(dr):
            dr.rounded_rectangle([90, 1400, W - 90, 1640], 36, fill=(255, 255, 255, 22))
            bb = dr.multiline_textbbox((0, 0), q["explain"], font=ef, spacing=14, align="center")
            ctext(dr, 1520 - (bb[3] - bb[1]) / 2 - bb[1], q["explain"], ef, WHITE + (255,), 14)
        im.alpha_composite(layer(e, a))

def q_sounds(T_COUNT, cd):
    # tic-tac d'horloge (2 clics par seconde) puis « ding » à la révélation
    s = [(T_COUNT + k / 2, 0.05, 2400 if k % 2 == 0 else 1800, 0.4, 120) for k in range(cd * 2)]
    return s + [(T_COUNT + cd, 0.6, 880, 0.35, 5), (T_COUNT + cd + 0.08, 0.6, 1320, 0.3, 5)]

def xp_sounds(t0):
    return [(t0 + j * 0.07, 0.25, fq, 0.25, 12) for j, fq in enumerate([660, 880, 1100, 1320])]

# ---------------------------------------------------------------- QUIZ (1 question)
def quiz(spec):
    cd = spec.get("countdown", 5)
    T_Q, T_OPT, T_COUNT = 1.6, 2.6, 3.2
    T_REVEAL = T_COUNT + cd; T_XP = T_REVEAL + 2.8; T_CTA = T_XP + 2.2; T_END = T_CTA + 2.8
    hookf = fit(spec["hook"], "Bold", 84, W - 160)
    fonts = q_fonts(spec)

    def frame(t, bg):
        im = bg.copy().convert("RGBA"); header(im, spec["badge"])
        if t < T_REVEAL + 0.4:
            a = prog(t, 0, 0.5) * (1 - prog(t, T_REVEAL, 0.4))
            y = 640 + 40 * (1 - prog(t, 0, 0.5)) if t < T_Q else 640 - 380 * prog(t, T_Q, 0.5)
            im.alpha_composite(layer(lambda dr: ctext(dr, y, spec["hook"], hookf, WHITE + (255,), 4), a))
        draw_question(im, t, spec, fonts, cd, T_Q, T_OPT, T_COUNT, T_XP, T_CTA)
        if T_XP <= t < T_CTA: xp_block(im, t, T_XP, T_CTA, spec.get("xp", 50))
        if t >= T_CTA: cta(im, t, T_CTA)
        return im.convert("RGB")

    return frame, q_sounds(T_COUNT, cd) + xp_sounds(T_XP), T_END

# ---------------------------------------------------------------- VOIX OFF (Fish Audio)
SR = 44100

def say(txt):
    """Texte écrit -> texte à lire (maths lisibles, sans retours à la ligne)."""
    for a, b in [("\n", " "), ("×", " fois "), ("÷", " divisé par "), ("²", " au carré"), ("³", " au cube"),
                 ("=", " égale "), ("≈", " environ "), ("•", ","), ("%", " pour cent")]:
        txt = txt.replace(a, b)
    return " ".join(txt.split())

def tts(text):
    """Voix off Fish Audio -> échantillons mono 16 bits à 44,1 kHz. None si FISH_API_KEY est absente."""
    key = os.environ.get("FISH_API_KEY")
    if not key: return None
    import array, urllib.request
    voice = os.environ.get("FISH_VOICE_ID")
    body = {"text": text, "format": "mp3", "mp3_bitrate": 128, "language": "fr", "prosody": {"speed": 1.15}}
    if voice: body["reference_id"] = voice
    req = urllib.request.Request("https://api.fish.audio/v1/tts", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "model": os.environ.get("FISH_MODEL", "s2.1-pro")})
    try:
        mp3 = urllib.request.urlopen(req, timeout=90).read()
    except Exception as e:
        sys.exit(f"Voix off Fish Audio en échec : {e}")
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         input=mp3, capture_output=True, check=True).stdout
    return array.array("h", pcm[: len(pcm) // 2 * 2])

def dur(clip): return len(clip) / SR if clip else 0.0

# ---------------------------------------------------------------- SÉRIE (plusieurs questions, >= 61 s)
# Style copié sur les quiz FR qui font 750 k – 950 k vues (analyse vidIQ 20/11/2026) : fond violet clair,
# carte blanche avec la question + une image, réponses en gros boutons blancs empilés (A. B. C.), barre de temps,
# les mauvaises réponses disparaissent et la bonne passe au vert. Fin (score, XP, « Rejoins la Ligue ») inchangée.
MIN_SERIE = 61.0  # monétisation TikTok : vidéos > 1 min
P_TOP = (160, 104, 220); P_BOT = (98, 56, 166); P_LETTER = (118, 64, 196); P_SHADOW = (66, 34, 120)
INK = (30, 26, 50); OK_GREEN = (46, 190, 96)
ORD = ["Première", "Deuxième", "Troisième", "Quatrième", "Cinquième", "Sixième", "Septième", "Huitième"]
IMG_W, IMG_H = 860, 470
CT = 340  # haut de la carte question (sous l'accroche)

_qbg = []
def quiz_bg():
    """Dégradé violet + motif de losanges discret (calculé une fois)."""
    if not _qbg:
        bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
        for y in range(H):
            k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(P_TOP[i] + (P_BOT[i] - P_TOP[i]) * k) for i in range(3)))
        pat = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pat)
        for j, y in enumerate(range(-60, H + 60, 120)):
            for x in range(-60 + (60 if j % 2 else 0), W + 60, 120):
                pd.polygon([(x, y - 34), (x + 34, y), (x, y + 34), (x - 34, y)], fill=(255, 255, 255, 16))
        bg = bg.convert("RGBA"); bg.alpha_composite(pat); _qbg.append(bg.convert("RGB"))
    return _qbg[0]

def q_image(q):
    """Image d'illustration : q["image"] (URL) ou q["image_query"] (recherche Openverse, domaine public / CC0
    uniquement, donc sans droits ni crédit). None si rien ne se charge : la carte se passe d'image."""
    import io, urllib.parse, urllib.request
    urls = [q["image"]] if q.get("image") else []
    if not urls and q.get("image_query"):
        api = ("https://api.openverse.org/v1/images/?license=cc0,pdm&mature=false&page_size=8&q="
               + urllib.parse.quote(q["image_query"]))
        try:
            req = urllib.request.Request(api, headers={"User-Agent": "revileague-reels/1.0"})
            res = json.load(urllib.request.urlopen(req, timeout=20))["results"]
            urls = [r["url"] for r in res if r.get("width", 0) >= 500]
        except Exception as e:
            print("Image : recherche échouée :", e)
    for u in urls[:4]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "revileague-reels/1.0"})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=20).read())).convert("RGB")
        except Exception:
            continue
        s = max(IMG_W / im.width, IMG_H / im.height)  # remplit la zone (recadrage centré)
        im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
        x, y = (im.width - IMG_W) // 2, (im.height - IMG_H) // 2
        im = im.crop((x, y, x + IMG_W, y + IMG_H)).convert("RGBA")
        m = Image.new("L", (IMG_W, IMG_H), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, IMG_W, IMG_H], 30, fill=255)
        im.putalpha(m); print("Image :", u); return im
    if q.get("image") or q.get("image_query"): print("Image : aucune image chargée pour", repr(q["question"]))
    return None

def serie(spec):
    qs = spec["questions"]; cd = spec.get("countdown", 5); n = len(qs)
    # voix off : accroche, « Deuxième question… », chaque question, chaque correction (+ appels à liker /
    # commenter comme les quiz qui percent), score, fin
    v_intro = tts(say(spec["hook"]))
    def intro_q(k):
        return "Dernière question, la plus dure ! " if k == n - 1 and n > 1 else ("" if k == 0 else f"{ORD[k]} question. ")
    v_q = [tts(intro_q(k) + (q.get("dit_question") or say(q["question"]))) for k, q in enumerate(qs)]
    BAIT = {0: "Like si tu as eu bon !", n // 2: "Écris GÉNIE en commentaire si tu as tout bon !"} if n > 2 else {}
    v_e = [tts((q.get("dit_explication") or say(f"Réponse {'ABCD'[q['answer']]} : {q['options'][q['answer']]}. {q['explain']}"))
               + (" " + BAIT[k] if k in BAIT else "")) for k, q in enumerate(qs)]
    v_score = tts(f"Alors, ton score sur {n} ? Dis-le en commentaire !")
    v_cta = tts("Révise comme dans un jeu. Rejoins la Ligue, lien en bio !")
    print("Voix off :", "oui" if v_intro else "non (FISH_API_KEY absente)")
    imgs = [q_image(q) for q in qs]

    # pas d'écran d'intro : la question 1 est à l'écran dès la 1re seconde, l'accroche au-dessus
    T_HOOK = dur(v_intro) + 0.1 if v_intro else 0.0
    T_CNT = [max(1.2, 0.3 + dur(v) + 0.2) + (T_HOOK if k == 0 else 0) for k, v in enumerate(v_q)]
    SEG = [c + cd + max(3.2 + (1.2 if k in BAIT else 0), 0.3 + dur(v) + 0.4) + 0.3
           for k, (c, v) in enumerate(zip(T_CNT, v_e))]
    S = [sum(SEG[:k]) for k in range(n)]
    T_SCORE = sum(SEG); T_XP = T_SCORE + max(2.4, 0.2 + dur(v_score) + 0.3); T_CTA = T_XP + 2.0
    T_END = T_CTA + max(2.6, 0.3 + dur(v_cta) + 0.3)
    if v_intro and T_END < MIN_SERIE:  # sans voix (Fish en panne) la vidéo est plus courte mais reste publiable
        sys.exit(f"Série trop courte ({T_END:.1f} s < {MIN_SERIE:.0f} s) : ajoute une question.")
    hookf = fit(spec["hook"], "Bold", 64, W - 120)
    QF = [fit(q["question"], "Bold", 84, W - 220) for q in qs]
    OF = [[fit(o, "Bold", 70, W - 330) for o in q["options"]] for q in qs]
    EF = [fit(q["explain"], "Medium", 50, W - 240) for q in qs]

    def layout(k):
        """Positions : haut de la carte, zone image, 1er bouton, hauteur et pas des boutons."""
        no = len(qs[k]["options"]); img = imgs[k] is not None
        bh, gap = (150, 30) if no <= 3 else (128, 22)
        card_bot = CT + 230 + (IMG_H + 30 if img else 0)
        return card_bot, card_bot + 40, bh, gap

    def draw_q(im, u, k):
        q = qs[k]; card_bot, oy, bh, gap = layout(k)
        T_REV = T_CNT[k] + cd; out = 1 - prog(u, SEG[k] - 0.35, 0.35)
        def card(dr):
            dr.rounded_rectangle([70, CT + 10, W - 70, card_bot + 10], 44, fill=P_SHADOW + (255,))
            dr.rounded_rectangle([70, CT, W - 70, card_bot], 44, fill=(255, 255, 255, 255))
            bb = dr.multiline_textbbox((0, 0), q["question"], font=QF[k], spacing=8, align="center")
            ctext(dr, CT + 115 - (bb[3] - bb[1]) / 2 - bb[1], q["question"], QF[k], INK + (255,), 8)
        im.alpha_composite(layer(card, prog(u, 0, 0.25) * out))
        if imgs[k] is not None:
            p = prog(u, 0.15, 0.35)
            if p * out > 0:
                L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); L.alpha_composite(imgs[k], ((W - IMG_W) // 2, CT + 230))
                if p * out < 1: L.putalpha(L.getchannel("A").point(lambda v: int(v * p * out)))
                im.alpha_composite(L)
        good = q["answer"]
        for i, opt in enumerate(q["options"]):
            ok = i == good
            ap = prog(u, 0.5 + i * 0.12, 0.3) * (1 if ok else 1 - prog(u, T_REV, 0.35)) * out
            if ap <= 0: continue
            y = oy + i * (bh + gap) + 40 * (1 - prog(u, 0.5 + i * 0.12, 0.3))
            if ok and u >= T_REV + 0.5:  # la bonne réponse remonte en 1re position
                y = oy + (y - oy) * (1 - prog(u, T_REV + 0.5, 0.4))
            green = ok and u >= T_REV
            def od(dr, y=y, opt=opt, i=i, green=green):
                dr.rounded_rectangle([90, y + 9, W - 90, y + bh + 9], 40, fill=(P_SHADOW if not green else (25, 120, 60)) + (255,))
                dr.rounded_rectangle([90, y, W - 90, y + bh], 40, fill=(OK_GREEN if green else (255, 255, 255)) + (255,))
                lf = F("Bold", 70 if bh >= 150 else 62)
                dr.text((140, y + bh / 2), "ABCD"[i] + ".", font=lf, fill=(WHITE if green else P_LETTER) + (255,), anchor="lm")
                dr.text((250, y + bh / 2), opt, font=OF[k][i], fill=(WHITE if green else INK) + (255,), anchor="lm")
            im.alpha_composite(layer(od, ap))
        if T_CNT[k] <= u < T_REV + 0.3:  # barre de temps qui se vide (jaune puis rouge)
            rem = max(0, T_REV - u); frac = rem / cd
            def bar(dr):
                dr.rounded_rectangle([90, 1800, W - 90, 1836], 18, fill=(255, 255, 255, 70))
                dr.rounded_rectangle([90, 1800, 90 + (W - 180) * frac, 1836], 18, fill=(GOLD if rem > 1.5 else RED) + (255,))
                dr.text((W / 2, 1755), str(math.ceil(rem)), font=F("Bold", 64), fill=WHITE + (255,), anchor="mm")
            im.alpha_composite(layer(bar, prog(u, T_CNT[k], 0.2) * (1 - prog(u, T_REV, 0.3))))
        if u >= T_REV + 0.7:  # correction sous la bonne réponse
            ey = oy + bh + gap + 10
            def ex(dr):
                bb = dr.multiline_textbbox((0, 0), q["explain"], font=EF[k], spacing=10, align="center")
                hh = bb[3] - bb[1] + 70
                dr.rounded_rectangle([90, ey, W - 90, ey + hh], 36, fill=(255, 255, 255, 235))
                ctext(dr, ey + 35 - bb[1], q["explain"], EF[k], INK + (255,), 10)
            im.alpha_composite(layer(ex, prog(u, T_REV + 0.7, 0.35) * out))
        if k in BAIT and u >= T_REV + 1.0:  # appel à liker / commenter (comme les quiz qui percent)
            def bt(dr):
                f = fit(BAIT[k], "Bold", 52, W - 260); tw = f.getlength(BAIT[k]) + 80
                dr.rounded_rectangle([(W - tw) / 2, 1700, (W + tw) / 2, 1800], 50, fill=GOLD + (255,))
                dr.text((W / 2, 1750), BAIT[k], font=f, fill=INK + (255,), anchor="mm")
            im.alpha_composite(layer(bt, back(u, T_REV + 1.0, 0.4) * out))

    def frame(t, bg):
        k = max([0] + [j for j in range(n) if S[j] <= t])
        if t < T_SCORE:
            im = quiz_bg().copy().convert("RGBA"); u = t - S[k]
            header(im, qs[k].get("badge", spec["badge"]))
            a = (1.0 if k == 0 else prog(u, 0, 0.3)) * (1 - prog(u, SEG[k] - 0.35, 0.35))
            def top(dr):
                if k == 0:  # l'accroche, pleine dès la 1re image
                    bb = dr.multiline_textbbox((0, 0), spec["hook"], font=hookf, spacing=4, align="center")
                    y = 250 - (bb[3] - bb[1]) / 2 - bb[1]
                    ctext(dr, y + 4, spec["hook"], hookf, P_SHADOW + (255,), 4); ctext(dr, y, spec["hook"], hookf, WHITE + (255,), 4)
                else:
                    txt = "Dernière question !" if k == n - 1 else f"Question {k + 1}/{n}"
                    ctext(dr, 214, txt, F("Bold", 66), P_SHADOW + (255,)); ctext(dr, 210, txt, F("Bold", 66), (GOLD if k == n - 1 else WHITE) + (255,))
            im.alpha_composite(layer(top, a))
            draw_q(im, u, k)
            return im.convert("RGB")
        im = bg.copy().convert("RGBA"); header(im, spec["badge"])  # fin inchangée
        if t < T_CTA:
            a = prog(t, T_SCORE, 0.5) * (1 - prog(t, T_CTA - 0.4, 0.4))
            im.alpha_composite(layer(lambda dr: ctext(dr, 640 + 40 * (1 - prog(t, T_SCORE, 0.5)),
                f"Ton score sur {n} ?", F("Bold", 100), GOLD + (255,)), a))
            im.alpha_composite(layer(lambda dr: ctext(dr, 820, "Dis-le en commentaire !", F("Medium", 56), WHITE + (255,)), a))
            if t >= T_XP: xp_block(im, t, T_XP, T_CTA, spec.get("xp", 50 * n))
        else:
            cta(im, t, T_CTA)
        return im.convert("RGB")

    sounds = []
    for k in range(n):
        sounds += [(S[k], 0.3, 700, 0.25, 8)] + [(S[k] + st, d, f, v, dc) for st, d, f, v, dc in q_sounds(T_CNT[k], cd)]
    sounds += [(T_SCORE, 0.5, 880, 0.3, 5)] + xp_sounds(T_XP)
    voices = [(0.3, v_intro), (T_SCORE + 0.2, v_score), (T_CTA + 0.3, v_cta)]
    voices += [(S[k] + 0.3 + (T_HOOK if k == 0 else 0), v_q[k]) for k in range(n)] + [(S[k] + T_CNT[k] + cd + 0.4, v_e[k]) for k in range(n)]
    return frame, sounds, T_END, [(s, c) for s, c in voices if c]

# ---------------------------------------------------------------- ASTUCE (plusieurs infos, voix off, >= 60 s)
MIN_ASTUCE = 61.0  # monétisation TikTok : vidéos > 1 min

def astuce(spec):
    infos = spec.get("infos") or [{k: spec[k] for k in ("title", "lines", "example") if k in spec}]
    n = len(infos)
    hook = spec.get("hook", f"{n} infos à connaître")
    v_intro = tts("Le savais-tu ? " + say(hook))
    def lire(info):
        txt = say(info["title"]); txt += "" if txt[-1:] in ".?!:" else "."
        for l in info["lines"]:
            l = say(l); txt += " " + l + ("" if l[-1:] in ".?!" else ".")
        return txt + " Exemple : " + say(info["example"]) + "."
    v_i = [tts(i.get("dit") or lire(i)) for i in infos]
    v_end = tts(f"Tu en connaissais combien sur {n} ? Dis-le en commentaire ! Révise comme dans un jeu, rejoins la Ligue, lien en bio !")
    print("Voix off :", "oui" if v_intro else "non (FISH_API_KEY absente)")

    T_INTRO = max(1.8, 0.2 + dur(v_intro) + 0.3)
    # par info : titre à 0,3 s, lignes réparties pendant la lecture, exemple, pause de lecture
    SEG = [max(4.0 + 1.6 * len(i["lines"]) + 3.0, 0.4 + dur(v) + 1.4) for i, v in zip(infos, v_i)]
    S = [T_INTRO + sum(SEG[:k]) for k in range(n)]
    T_XP = T_INTRO + sum(SEG); T_CTA = T_XP + 2.2
    T_END = max(T_CTA + 3.0, T_XP + 0.2 + dur(v_end) + 0.6)
    if v_intro and T_END < MIN_ASTUCE:  # sans voix la vidéo reste publiable
        sys.exit(f"Astuce trop courte ({T_END:.1f} s < {MIN_ASTUCE:.0f} s) : ajoute une info.")
    hookf = fit(hook, "Bold", 112, W - 140)
    F_T = [fit(i["title"], "Bold", 92, W - 260) for i in infos]
    F_L = [[fit(l, "Medium", 50, W - 300) for l in i["lines"]] for i in infos]
    F_E = [fit(i["example"], "Bold", 54, W - 260) for i in infos]
    # instants d'apparition (relatifs au début de l'info), calés sur la voix si elle existe
    def times(k):
        nl = len(infos[k]["lines"]); span = (SEG[k] - 1.4) if v_i[k] else (2.0 + 1.6 * nl)
        step = span / (nl + 1.6); return [1.0 + step * (j + 0.4) for j in range(nl)], 1.0 + step * (nl + 0.4)
    TM = [times(k) for k in range(n)]

    def frame(t, bg):
        k = max([0] + [j for j in range(n) if S[j] <= t])
        badge = infos[k].get("badge", spec["badge"]) if T_INTRO <= t < T_XP else spec["badge"]
        bg, tint = bg_for(badge); im = bg.copy().convert("RGBA"); deco(im, t, tint)
        header(im, badge)
        if t < T_INTRO:
            a = 1 - prog(t, T_INTRO - 0.3, 0.3); dy = 0  # accroche pleine dès la 1re image
            im.alpha_composite(layer(lambda dr: ctext(dr, 560 + dy, "Le savais-tu ?", F("Bold", 100), CYAN + (255,)), a))
            im.alpha_composite(layer(lambda dr: ctext(dr, 760 + dy, hook, hookf, WHITE + (255,), 4), a))
        elif t < T_XP:
            u = t - S[k]; out = 1 - prog(u, SEG[k] - 0.4, 0.4)
            a = prog(u, 0, 0.4) * out
            def pr(dr):
                ctext(dr, 220, f"Le savais-tu ?  {k + 1}/{n}", F("Bold", 64), CYAN + (255,))
                x0 = (W - (n * 44 - 16)) / 2
                for j in range(n):
                    dr.rounded_rectangle([x0 + j * 44, 330, x0 + j * 44 + 28, 346], 8,
                                         fill=GOLD + (255,) if j <= k else (255, 255, 255, 40))
            im.alpha_composite(layer(pr, a))
            info = infos[k]; tl, te = TM[k]
            a = prog(u, 0.3, 0.5) * out
            def td(dr):
                dr.rounded_rectangle([90, 420, W - 90, 680], 40, fill=CARD + (255,), outline=(70, 85, 130, 255), width=4)
                bb = dr.multiline_textbbox((0, 0), info["title"], font=F_T[k], spacing=6, align="center")
                ctext(dr, 550 - (bb[3] - bb[1]) / 2 - bb[1], info["title"], F_T[k], GOLD + (255,), 6)
            im.alpha_composite(layer(td, a))
            for i, l in enumerate(info["lines"]):
                if u >= tl[i]:
                    p = prog(u, tl[i], 0.45); y = 760 + i * 150 + 30 * (1 - p)
                    def ld(dr, l=l, y=y, f=F_L[k][i], i=i):
                        dr.ellipse([110, y + 22, 150, y + 62], fill=GOLD + (255,))
                        dr.text((130, y + 42), str(i + 1), font=F("Bold", 28), fill=NAVY + (255,), anchor="mm")
                        dr.multiline_text((180, y + 6), l, font=f, fill=WHITE + (255,), spacing=6)
                    im.alpha_composite(layer(ld, p * out))
            if u >= te:
                p = prog(u, te, 0.45); y0 = 790 + len(info["lines"]) * 150
                def ed(dr):
                    dr.rounded_rectangle([90, y0, W - 90, y0 + 220], 36, fill=GREEN + (60,), outline=GREEN + (255,), width=4)
                    ctext(dr, y0 + 22, "Exemple", F("Medium", 40), (180, 255, 210, 255))
                    bb = dr.multiline_textbbox((0, 0), info["example"], font=F_E[k], spacing=8, align="center")
                    ctext(dr, y0 + 140 - (bb[3] - bb[1]) / 2 - bb[1], info["example"], F_E[k], WHITE + (255,), 8)
                im.alpha_composite(layer(ed, p * out))
        elif t < T_CTA:
            a = prog(t, T_XP, 0.5) * (1 - prog(t, T_CTA - 0.4, 0.4))
            im.alpha_composite(layer(lambda dr: ctext(dr, 640, f"Tu en connaissais\ncombien sur {n} ?", F("Bold", 90), GOLD + (255,), 8), a))
            xp_block(im, t, T_XP, T_CTA, spec.get("xp", 20 * n))
        else:
            cta(im, t, T_CTA)
        return im.convert("RGB")

    sounds = []
    for k in range(n):
        tl, te = TM[k]
        sounds += [(S[k] + 0.3, 0.4, 700, 0.3, 8)] + [(S[k] + x, 0.15, 1000, 0.2, 30) for x in tl]
        sounds += [(S[k] + te, 0.5, 880, 0.25, 6), (S[k] + te + 0.08, 0.5, 1320, 0.2, 6)]
    sounds += xp_sounds(T_XP)
    voices = [(0.3, v_intro), (T_XP + 0.2, v_end)] + [(S[k] + 0.3, v_i[k]) for k in range(n)]
    return frame, sounds, T_END, [(s, c) for s, c in voices if c]

# ---------------------------------------------------------------- MUSIQUE DE FOND (synthétisée, libre de droits)
def music(T_END, voice_spans):
    """Boucle pop/lo-fi originale à 100 BPM (Am-F-C-G), baissée automatiquement sous la voix off."""
    import random
    rnd = random.Random(7); beat = 0.6; bar = 4 * beat; L = int(4 * bar * SR)
    loop = [0.0] * L
    def add(t0, d, fn):
        i0 = int(t0 * SR)
        for j in range(int(d * SR)):
            if i0 + j >= L: break
            loop[i0 + j] += fn(j / SR)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]  # Am F C G
    for b, ch in enumerate(chords):
        t0 = b * bar
        for m in ch:  # nappe douce
            f = hz(m); add(t0, bar, lambda x, f=f: 0.035 * min(1, x / 0.3) * min(1, (bar - x) / 0.3) * math.sin(2 * math.pi * f * x))
        for s in (0, 2):  # basse
            f = hz(ch[0] - 12); add(t0 + s * beat, beat * 1.8, lambda x, f=f: 0.12 * math.exp(-2.2 * x) * math.sin(2 * math.pi * f * x))
        arp = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12]
        for e in range(8):  # arpège en croches
            f = hz(arp[e % 4]); add(t0 + e * beat / 2, 0.28, lambda x, f=f: 0.035 * math.exp(-9 * x) * math.sin(2 * math.pi * f * x))
        for s in range(4):  # kick + charleston
            add(t0 + s * beat, 0.25, lambda x: 0.22 * math.exp(-14 * x) * math.sin(2 * math.pi * (50 * x + 35 * (1 - math.exp(-30 * x)))))
            add(t0 + s * beat + beat / 2, 0.05, lambda x: 0.025 * math.exp(-60 * x) * (rnd.random() * 2 - 1))
    N = int(T_END * SR); out = [0.0] * N
    gain = [1.0] * (int(T_END * 20) + 2)  # enveloppe à 20 Hz : 0,3 sous la voix
    for s, d in voice_spans:
        for g in range(max(0, int((s - 0.15) * 20)), min(len(gain), int((s + d + 0.2) * 20) + 1)): gain[g] = 0.3
    sm = gain[:]  # lissage
    for g in range(1, len(sm)): sm[g] = sm[g - 1] + (gain[g] - sm[g - 1]) * 0.35
    fade = 1.0
    for i in range(N):
        tt = i / SR; fade = min(1, tt / 1.0, (T_END - tt) / 1.5)
        out[i] = loop[i % L] * sm[int(tt * 20)] * max(0, fade)
    return out

# ---------------------------------------------------------------- COUVERTURE (1re image = miniature Instagram / TikTok)
COVER = 0.2  # secondes affichées au début ; les plateformes prennent la 1re image comme miniature

def cover(spec, bg):
    defi = spec.get("badge", "").upper().startswith("DÉFI")
    kicker = spec.get("cover_title") or ("DÉFI DE LA LIGUE" if defi else
                                         {"astuce": "LE SAVAIS-TU ?", "serie": "QUIZ"}.get(spec["type"], "QUESTION DU JOUR"))
    hook = spec.get("hook", "")
    n = len(spec.get("questions") or spec.get("infos") or [1])
    xp = spec.get("xp", 50)
    im = bg.copy().convert("RGBA"); header(im, spec.get("badge", ""))
    kf = fit(kicker, "Bold", 120, W - 160); hf = fit(hook, "Bold", 96, W - 220)
    def c(dr):
        dr.rounded_rectangle([60, 420, W - 60, 1380], 60, fill=CARD + (235,), outline=GOLD + (255,), width=6)
        ctext(dr, 500, kicker, kf, GOLD + (255,))
        dr.rounded_rectangle([W / 2 - 180, 660, W / 2 + 180, 668], 4, fill=CYAN + (255,))
        bb = dr.multiline_textbbox((0, 0), hook, font=hf, spacing=12, align="center")
        ctext(dr, 960 - (bb[3] - bb[1]) / 2 - bb[1], hook, hf, WHITE + (255,), 12)
        pill = f"{n} {'défis' if defi else 'questions'}  •  +{xp} XP" if spec["type"] == "serie" else (
               f"{n} infos  •  +{xp} XP" if spec["type"] == "astuce" else f"+{xp} XP")
        pf = F("Bold", 56); pw = pf.getlength(pill) + 100
        dr.rounded_rectangle([(W - pw) / 2, 1230, (W + pw) / 2, 1330], 50, fill=GOLD + (255,))
        dr.text((W / 2, 1280), pill, font=pf, fill=NAVY + (255,), anchor="mm")
        ctext(dr, 1560, "Révise comme dans un jeu", F("Bold", 64), WHITE + (255,))
        ctext(dr, 1660, "de la 6e à la Terminale", F("Medium", 48), GREY + (255,))
    im.alpha_composite(layer(c, 1))
    return im.convert("RGB")

# ---------------------------------------------------------------- RENDU
def render(spec, out):
    check_glyphs(spec)
    frame, sounds, T_END, *voices = {"quiz": quiz, "serie": serie, "astuce": astuce}[spec["type"]](spec)
    N = int(SR * T_END); buf = [0.0] * N
    duck = 0.45 if voices and voices[0] else 1.0  # bips plus discrets sous la voix
    sounds = [(s, d, f, v * duck, dc) for s, d, f, v, dc in sounds]
    for start, clip in (voices[0] if voices else []):
        i0 = int(start * SR)
        for j, v in enumerate(clip[: max(0, N - i0)]):
            buf[i0 + j] += v / 32768 * 0.9
    for start, d_s, freq, vol, decay in sounds:
        for k in range(int(d_s * SR)):
            i = int(start * SR) + k
            if i >= N: break
            tt = k / SR; buf[i] += vol * math.sin(2 * math.pi * freq * tt) * math.exp(-decay * tt)
    bed = music(T_END, [(s, dur(c)) for s, c in (voices[0] if voices else [])])
    for i in range(N): buf[i] += bed[i]
    wav = out + ".wav"
    with wave.open(wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 30000)) for v in buf))
    bg = make_bg()
    cov = cover(spec, bg); cov.save(os.path.splitext(out)[0] + "-cover.jpg", quality=92)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for n in range(int(T_END * FPS)):
        p.stdin.write((cov if n / FPS < COVER else frame(n / FPS, bg)).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    if p.returncode: sys.exit("ffmpeg a échoué")
    print("OK", out, f"{T_END:.1f}s")

if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
