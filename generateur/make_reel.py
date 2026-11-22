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

ORDINAUX = {1: "premier", 2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième", 6: "sixième", 7: "septième",
            8: "huitième", 9: "neuvième", 10: "dixième", 11: "onzième", 12: "douzième"}
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]

def say(txt):
    """Texte écrit -> texte que la voix lit bien : « 8/8 » -> « 8 sur 8 », « 3e » -> « troisième », dates, heures,
    sigles, symboles ; un retour à la ligne devient une petite pause. Les accents et la ponctuation sont gardés."""
    import re
    txt = "".join(c for c in txt if ord(c) < 0x2190 or c in "→•…≈×÷")  # retire les emojis
    txt = re.sub(r"(?<![.,;:!?…])\s*\n\s*(?=[A-ZÀ-Ý(])", ", ", txt.strip())  # nouvelle phrase à la ligne = pause
    txt = txt.replace("\n", " ")
    txt = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
                 lambda m: f"{'1er' if m[1] in ('1', '01') else int(m[1])} {MOIS[int(m[2]) - 1]} {m[3]}"
                 if 1 <= int(m[2]) <= 12 else m[0], txt)
    txt = re.sub(r"\bkm/h\b", "kilomètres heure", txt).replace("n°", "numéro ")
    txt = re.sub(r"(\d)\s*/\s*(\d)", r"\1 sur \2", txt)  # score ou note : 8/8, 12/20 (jamais « huitièmes »)
    txt = re.sub(r"\b(\d{1,2})h(\d{2})\b", r"\1 heures \2", txt)
    txt = re.sub(r"\b(\d{1,2})h\b", r"\1 heures", txt)
    txt = re.sub(r"\b1(?:er|re|ère)\b", lambda m: "première" if m[0] != "1er" else "premier", txt)
    txt = re.sub(r"\b(\d{1,2})(?:e|ème|eme)\b", lambda m: ORDINAUX.get(int(m[1]), m[1] + "ième"), txt)
    for a, b in [("Tle", "terminale"), ("2nde", "seconde"), ("2nd", "second"), ("BO", "Bulletin officiel"),
                 ("DNB", "brevet"), ("TB", "très bien"), ("AB", "assez bien"), ("n°", "numéro "), ("ex.", "par exemple"),
                 ("env.", "environ")]:
        txt = re.sub(r"(?<!\w)" + re.escape(a) + r"(?!\w)", b, txt)
    for a, b in [("×", " fois "), ("÷", " divisé par "), ("²", " au carré"), ("³", " au cube"), ("=", " égale "),
                 ("≈", " environ "), ("•", ","), ("→", ", donc "), ("%", " pour cent"), ("€", " euros"),
                 ("°C", " degrés Celsius"), ("°", " degrés"), ("&", " et "), (" - ", ", "), ("«", ""), ("»", "")]:
        txt = txt.replace(a, b)
    txt = re.sub(r"(\d)\+(\d)", r"\1 plus \2", txt.replace(" + ", " plus "))
    txt = re.sub(r"\b[A-ZÀ-Ý]{5,}\b", lambda m: m[0].lower(), txt)  # MOTS EN CAPITALES lus normalement (sigles courts gardés)
    txt = re.sub(r"\s+([,.])", r"\1", " ".join(txt.split()))
    return re.sub(r",\s*,", ",", txt)

def _test_say():
    assert say("Impossible d'avoir 8/8") == "Impossible d'avoir 8 sur 8", say("Impossible d'avoir 8/8")
    assert say("Brevet 2027 :\nta moyenne de 3e\ncompte pour 40 %") == "Brevet 2027 : ta moyenne de troisième compte pour 40 pour cent"
    assert say("La n°4 : x² + 3 = 12") == "La numéro 4 : x au carré plus 3 égale 12"
    assert say("Philo le 14/06/2027 à 8h") == "Philo le 14 juin 2027 à 8 heures"
    assert say("12 AB • 14 B • 16 TB") == "12 assez bien, 14 B, 16 très bien"
    assert say("élève de 1re et de Tle, OFFICIEL") == "élève de première et de terminale, officiel"

def tts(text):
    """Voix off Fish Audio -> échantillons mono 16 bits à 44,1 kHz. None si FISH_API_KEY est absente."""
    key = os.environ.get("FISH_API_KEY")
    if not key: return None
    import array, urllib.request
    voice = os.environ.get("FISH_VOICE_ID")
    text = say(text)  # toujours normalisé, même pour les « dit » écrits à la main
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
P_TOP = (160, 104, 220); P_BOT = (98, 56, 166); P_LETTER = (36, 62, 150); P_SHADOW = (28, 36, 60)  # thème cahier (20/11 : comme l'Info brevet)
INK = (30, 26, 50); OK_GREEN = (46, 190, 96)
ORD = ["Première", "Deuxième", "Troisième", "Quatrième", "Cinquième", "Sixième", "Septième", "Huitième"]
IMG_W, IMG_H = 860, 470
CT = 370  # haut de la carte question (sous le bandeau)

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

def q_image(q, size=None, radius=30):
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
            urls = [r["url"] for r in res if (r.get("width") or 0) >= 500]
        except Exception as e:
            print("Image : recherche échouée :", e)
    for u in urls[:4]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "revileague-reels/1.0"})
            im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=20).read())).convert("RGB")
        except Exception:
            continue
        tw, th = size or (IMG_W, IMG_H)
        s = max(tw / im.width, th / im.height)  # remplit la zone (recadrage centré)
        im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
        x, y = (im.width - tw) // 2, (im.height - th) // 2
        im = im.crop((x, y, x + tw, y + th)).convert("RGBA")
        if radius:
            m = Image.new("L", (tw, th), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, tw, th], radius, fill=255); im.putalpha(m)
        print("Image :", u); return im
    if q.get("image") or q.get("image_query"): print("Image : aucune image chargée pour", repr(q.get("question", "la couverture")))
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
    hookf = fit(spec["hook"], "Bold", 60, W - 180)
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
            dr.rounded_rectangle([70, CT, W - 70, card_bot], 44, fill=(255, 255, 255, 255), outline=P_SHADOW + (255,), width=5)
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
                dr.rounded_rectangle([90, y, W - 90, y + bh], 40, fill=(OK_GREEN if green else (255, 255, 255)) + (255,),
                                     outline=((25, 120, 60) if green else P_SHADOW) + (255,), width=4)
                lf = F("Bold", 70 if bh >= 150 else 62)
                dr.text((140, y + bh / 2), "ABCD"[i] + ".", font=lf, fill=(WHITE if green else P_LETTER) + (255,), anchor="lm")
                dr.text((250, y + bh / 2), opt, font=OF[k][i], fill=(WHITE if green else INK) + (255,), anchor="lm")
            im.alpha_composite(layer(od, ap))
        if T_CNT[k] <= u < T_REV + 0.3:  # barre de temps qui se vide (jaune puis rouge)
            rem = max(0, T_REV - u); frac = rem / cd
            def bar(dr):
                dr.rounded_rectangle([90, 1800, W - 90, 1836], 18, fill=P_SHADOW + (40,))
                dr.rounded_rectangle([90, 1800, 90 + (W - 180) * frac, 1836], 18, fill=(GOLD if rem > 1.5 else RED) + (255,))
                dr.text((W / 2, 1755), str(math.ceil(rem)), font=F("Bold", 64), fill=P_SHADOW + (255,), anchor="mm")
            im.alpha_composite(layer(bar, prog(u, T_CNT[k], 0.2) * (1 - prog(u, T_REV, 0.3))))
        if u >= T_REV + 0.7:  # correction sous la bonne réponse
            ey = oy + bh + gap + 10
            def ex(dr):
                bb = dr.multiline_textbbox((0, 0), q["explain"], font=EF[k], spacing=10, align="center")
                hh = bb[3] - bb[1] + 70
                dr.rounded_rectangle([90, ey, W - 90, ey + hh], 36, fill=(255, 255, 255, 255), outline=(200, 206, 222, 255), width=3)
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
            im = paper_bg().copy().convert("RGBA"); u = t - S[k]
            im.alpha_composite(layer(lambda dr: dr.rounded_rectangle([60, 70, 520, 160], 45, fill=NAVY2 + (255,)), 1))
            header(im, qs[k].get("badge", spec["badge"]))
            a = (1.0 if k == 0 else prog(u, 0, 0.3)) * (1 - prog(u, SEG[k] - 0.35, 0.35))
            def banner(dr):  # bandeau bleu nuit, comme l'Info brevet
                dr.rounded_rectangle([60, 185 + 8, W - 60, 345 + 8], 36, fill=(10, 14, 26, 255))
                dr.rounded_rectangle([60, 185, W - 60, 345], 36, fill=NAVY2 + (255,))
            im.alpha_composite(layer(banner, 1))
            def top(dr):
                if k == 0:  # l'accroche, pleine dès la 1re image, 1re ligne en or
                    ls = spec["hook"].split(chr(10)); lh = hookf.size * 1.2; y = 265 - lh * len(ls) / 2
                    for i, l in enumerate(ls):
                        dr.text((W / 2, y + i * lh + lh / 2), l, font=hookf, fill=(GOLD if i == 0 else WHITE) + (255,), anchor="mm")
                else:
                    txt = "Dernière question !" if k == n - 1 else f"Question {k + 1}/{n}"
                    dr.text((W / 2, 265), txt, font=F("Bold", 66), fill=(GOLD if k == n - 1 else WHITE) + (255,), anchor="mm")
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

# ---------------------------------------------------------------- INFO (info officielle brevet / bac, >= 61 s)
# Format inspiré des comptes « infos brevet » qui font beaucoup d'enregistrements : accroche « alerte » dans un
# bandeau, tableau dont les lignes se dévoilent (flou -> net) au rythme de la voix, conseil concret, source
# officielle. Fond cahier à carreaux aux couleurs RéviLeague. Fin (question, XP, « Rejoins la Ligue ») inchangée.
MIN_INFO = 61.0
PAPER = (247, 243, 234); GRID = (214, 226, 240); INK_BLUE = (36, 62, 150)

_pbg = []
def paper_bg():
    if not _pbg:
        bg = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(bg)
        for x in range(0, W, 54): d.line([(x, 0), (x, H)], fill=GRID, width=2)
        for y in range(0, H, 54): d.line([(0, y), (W, y)], fill=GRID, width=2)
        _pbg.append(bg)
    return _pbg[0]

def info(spec):
    rows = spec["rows"]; n = len(rows)
    v_hook = tts(say(spec["hook"]))
    v_r = [tts(r.get("dit") or say(f"{r['label']} : {r['value']}.")) for r in rows]
    v_c = tts(spec.get("dit_conseil") or "Mon conseil : " + say(spec["conseil"]))
    v_q = tts(say(spec.get("question", "Tu le savais ?")) + " Dis-le en commentaire !")
    v_cta = tts("Révise comme dans un jeu. Rejoins la Ligue, lien en bio !")
    print("Voix off :", "oui" if v_hook else "non (FISH_API_KEY absente)")

    T0 = max(2.6, 0.3 + dur(v_hook) + 0.3)            # 1re ligne dévoilée après l'accroche
    RS = [max(2.8, 0.3 + dur(v) + 0.5) for v in v_r]
    R = [T0 + sum(RS[:k]) for k in range(n)]
    T_C = T0 + sum(RS); T_END_INFO = T_C + max(4.0, 0.3 + dur(v_c) + 1.2)
    T_Q = T_END_INFO; T_XP = T_Q + max(2.4, 0.2 + dur(v_q) + 0.3); T_CTA = T_XP + 2.0
    T_END = T_CTA + max(2.6, 0.3 + dur(v_cta) + 0.3)
    if v_hook and T_END < MIN_INFO:
        sys.exit(f"Info trop courte ({T_END:.1f} s < {MIN_INFO:.0f} s) : ajoute une ligne.")

    hook_lines = spec["hook"].split("\n")
    hookf = fit(spec["hook"], "Bold", 78, W - 200)
    LF = F("Medium", 40); VF = [fit(r["value"], "Bold", 56, W - 520) for r in rows]
    CF = fit(spec["conseil"], "Bold", 50, W - 260)
    TY, HH, RH = 660, 90, 128  # haut du tableau, en-tête, hauteur d'une ligne
    TB = TY + HH + n * RH

    def value_patch(k, blur):
        P = Image.new("RGBA", (W - 420, RH), (0, 0, 0, 0))
        ImageDraw.Draw(P).text((0, RH / 2), rows[k]["value"], font=VF[k], fill=INK_BLUE + (255,), anchor="lm")
        return P.filter(ImageFilter.GaussianBlur(blur)) if blur > 0.3 else P

    def frame(t, bg):
        if t >= T_END_INFO:  # fin identique aux autres formats
            im = bg.copy().convert("RGBA"); header(im, spec["badge"])
            if t < T_CTA:
                a = prog(t, T_Q, 0.5) * (1 - prog(t, T_CTA - 0.4, 0.4))
                im.alpha_composite(layer(lambda dr: ctext(dr, 640 + 40 * (1 - prog(t, T_Q, 0.5)),
                    spec.get("question", "Tu le savais ?"), fit(spec.get("question", "Tu le savais ?"), "Bold", 96, W - 160), GOLD + (255,)), a))
                im.alpha_composite(layer(lambda dr: ctext(dr, 840, "Dis-le en commentaire !", F("Medium", 56), WHITE + (255,)), a))
                if t >= T_XP: xp_block(im, t, T_XP, T_CTA, spec.get("xp", 100))
            else:
                cta(im, t, T_CTA)
            return im.convert("RGB")
        im = paper_bg().copy().convert("RGBA"); out = 1 - prog(t, T_END_INFO - 0.4, 0.4)
        im.alpha_composite(layer(lambda dr: dr.rounded_rectangle([60, 70, 520, 160], 45, fill=NAVY2 + (255,)), 1))  # logo lisible sur fond clair
        header(im, spec["badge"])
        def banner(dr):  # accroche, 1re ligne en or
            dr.rounded_rectangle([60, 210 + 10, W - 60, 580 + 10], 40, fill=(10, 14, 26, 255))
            dr.rounded_rectangle([60, 210, W - 60, 580], 40, fill=NAVY2 + (255,))
            lh = hookf.size * 1.25; y = 395 - lh * len(hook_lines) / 2
            for i, l in enumerate(hook_lines):
                dr.text((W / 2, y + i * lh + lh / 2), l, font=hookf, fill=(GOLD if i == 0 else WHITE) + (255,), anchor="mm")
        im.alpha_composite(layer(banner, out))
        if spec.get("stamp"):  # tampon rouge penché
            sp = back(t, 0.5, 0.4); sf = F("Bold", 40); sw = int(sf.getlength(spec["stamp"]) + 60)
            S = Image.new("RGBA", (sw + 20, 100), (0, 0, 0, 0)); sd = ImageDraw.Draw(S)
            sd.rounded_rectangle([10, 10, sw + 10, 90], 14, outline=RED + (255,), width=6)
            sd.text((sw / 2 + 10, 50), spec["stamp"], font=sf, fill=RED + (255,), anchor="mm")
            S = S.rotate(-8, expand=True, resample=Image.BICUBIC)
            if sp * out < 1: S.putalpha(S.getchannel("A").point(lambda v: int(v * max(0, min(1, sp * out)))))
            im.alpha_composite(S, (W - 60 - S.width + 10, 592 - S.height // 2))
        def table(dr):
            dr.rounded_rectangle([70, TY + 10, W - 70, TB + 10], 30, fill=NAVY2 + (255,))
            dr.rounded_rectangle([70, TY, W - 70, TB], 30, fill=(255, 255, 255, 255), outline=NAVY2 + (255,), width=5)
            dr.rounded_rectangle([75, TY + 5, W - 75, TY + HH], 26, fill=(232, 236, 247, 255))
            dr.text((110, TY + HH / 2 + 3), spec.get("table_title", ""), font=F("Bold", 40), fill=NAVY + (255,), anchor="lm")
            dr.text((W - 110, TY + HH / 2 + 3), spec.get("table_tag", ""), font=F("Medium", 36), fill=GREY + (255,), anchor="rm")
            for k, r in enumerate(rows):
                y = TY + HH + k * RH
                if k: dr.line([(90, y), (W - 90, y)], fill=(225, 228, 238, 255), width=3)
                dr.text((110, y + RH / 2), r["label"], font=LF, fill=(90, 96, 120, 255), anchor="lm")
            dr.line([(400, TY + HH), (400, TB - 10)], fill=(225, 228, 238, 255), width=3)
        im.alpha_composite(layer(table, prog(t, 0.2, 0.4) * out))
        for k in range(n):  # valeurs floues tant qu'elles ne sont pas lues
            p = prog(t, R[k], 0.5)
            P = value_patch(k, 16 * (1 - p))
            if k == max([j for j in range(n) if R[j] <= t] or [-1]) and t < T_C:  # ligne en cours surlignée
                im.alpha_composite(layer(lambda dr, k=k: dr.rectangle([78, TY + HH + k * RH + 6, W - 78, TY + HH + (k + 1) * RH - 6],
                                                                       fill=GOLD + (60,)), out))
            if out < 1: P.putalpha(P.getchannel("A").point(lambda v: int(v * out)))
            im.alpha_composite(P, (428, TY + HH + k * RH))
        if t >= T_C:
            def tip(dr):
                y0 = TB + 50
                bb = dr.multiline_textbbox((0, 0), spec["conseil"], font=CF, spacing=10, align="center")
                h = bb[3] - bb[1] + 150
                dr.rounded_rectangle([70, y0 + 10, W - 70, y0 + h + 10], 30, fill=(200, 150, 30, 255))
                dr.rounded_rectangle([70, y0, W - 70, y0 + h], 30, fill=GOLD + (255,))
                ctext(dr, y0 + 22, "LE CONSEIL", F("Bold", 40), NAVY + (255,))
                ctext(dr, y0 + 90 - bb[1], spec["conseil"], CF, NAVY + (255,), 10)
            im.alpha_composite(layer(tip, back(t, T_C, 0.45) * out))
        if spec.get("source"):
            im.alpha_composite(layer(lambda dr: ctext(dr, 1835, "Source : " + spec["source"], F("Medium", 32), (110, 116, 140, 255)), out))
        return im.convert("RGB")

    sounds = [(R[k], 0.25, 1100, 0.3, 14) for k in range(n)] + [(T_C, 0.5, 880, 0.3, 6), (T_C + 0.08, 0.5, 1320, 0.25, 6)]
    sounds += [(T_Q, 0.5, 880, 0.3, 5)] + xp_sounds(T_XP)
    voices = [(0.3, v_hook), (T_C + 0.3, v_c), (T_Q + 0.2, v_q), (T_CTA + 0.3, v_cta)] + [(R[k], v_r[k]) for k in range(n)]
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
    """Miniature (style choisi le 22/11/2026) : photo plein écran en rapport avec le sujet, assombrie, logo + badge
    en haut, un encadré bleu nuit avec le type de vidéo (en or) et UNIQUEMENT le sujet de la vidéo, tampon rouge.
    Photo : spec["cover_image"] (URL) ou spec["cover_image_query"] ; à défaut la 1re question (série) ;
    sans photo, fond cahier."""
    defi = spec.get("badge", "").upper().startswith("DÉFI")
    typ = spec["type"]
    kicker = spec.get("cover_title") or ("DÉFI DE LA LIGUE" if defi else
                                         {"astuce": "LE SAVAIS-TU ?", "serie": "QUIZ DU JOUR"}.get(typ, "INFO BREVET / BAC"))
    stamp = spec.get("stamp") or ("DÉFI" if defi else {"serie": "QUIZ"}.get(typ, "À SAVOIR"))
    text = spec.get("cover_text") or spec.get("hook", "")
    src = ({"image": spec.get("cover_image"), "image_query": spec.get("cover_image_query")}
           if spec.get("cover_image") or spec.get("cover_image_query") else (spec.get("questions") or [{}])[0])
    photo = q_image(src, size=(W, H), radius=0) if (src.get("image") or src.get("image_query")) else None
    im = photo if photo is not None else paper_bg().copy().convert("RGBA")
    im.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 26, 150 if photo is not None else 0)))
    im.alpha_composite(layer(lambda dr: dr.rounded_rectangle([60, 70, 520, 160], 45, fill=NAVY2 + (255,)), 1))
    header(im, spec.get("badge", ""))
    kf = fit(kicker, "Bold", 96, W - 220); tf = fit(text, "Bold", 120, W - 220)
    def c(dr):
        bb = dr.multiline_textbbox((0, 0), text, font=tf, spacing=10, align="center")
        th = bb[3] - bb[1]; top = 960 - (190 + th) / 2
        dr.rounded_rectangle([60, top, W - 60, top + 190 + th + 70], 50, fill=NAVY2 + (215,))
        ctext(dr, top + 60, kicker, kf, GOLD + (255,))
        ctext(dr, top + 190 - bb[1], text, tf, WHITE + (255,), 10)
        c.top = top
    im.alpha_composite(layer(c, 1))
    sf = F("Bold", 54); sw = int(sf.getlength(stamp) + 80)
    S = Image.new("RGBA", (sw + 20, 128), (0, 0, 0, 0)); sd = ImageDraw.Draw(S)
    sd.rounded_rectangle([10, 10, sw + 10, 118], 18, fill=(255, 255, 255, 235), outline=RED + (255,), width=8)
    sd.text((sw / 2 + 10, 64), stamp, font=sf, fill=RED + (255,), anchor="mm")
    S = S.rotate(-8, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(S, (W - 90 - S.width, int(c.top - S.height / 2 + 10)))
    return im.convert("RGB")

# ---------------------------------------------------------------- CARROUSEL PHOTO « Le savais-tu ? » (5 images 4:5)
# Post photo (pas une vidéo) : 1 couverture, 3 infos, 1 « Abonne-toi ! ». Même look cahier que les vidéos.
CW, CH = 1080, 1350

def carrousel(spec, out):
    """Écrit <out sans extension>-1.jpg … -5.jpg et renvoie la liste des fichiers."""
    infos = spec["infos"]
    if len(infos) != 3: sys.exit("Le carrousel attend exactement 3 infos.")
    base = os.path.splitext(out)[0]; files = []
    def page(draw_fn, badge, k):
        im = paper_bg().crop((0, 0, CW, CH)).convert("RGBA")
        L = Image.new("RGBA", (CW, CH), (0, 0, 0, 0)); dr = ImageDraw.Draw(L)
        dr.rounded_rectangle([60, 60, 520, 150], 45, fill=NAVY2 + (255,))
        dr.text((95, 78), "Révi", font=F("Bold", 50), fill=WHITE)
        dr.text((95 + F("Bold", 50).getlength("Révi"), 78), "League", font=F("Bold", 50), fill=GOLD)
        f = F("Bold", 38); bw = f.getlength(badge) + 60
        dr.rounded_rectangle([CW - 60 - bw, 72, CW - 60, 138], 33, fill=CYAN + (255,))
        dr.text((CW - 60 - bw + 30, 80), badge, font=f, fill=NAVY)
        x0 = CW / 2 - 5 * 18  # points de pagination
        for j in range(5):
            dr.ellipse([x0 + j * 36, CH - 70, x0 + j * 36 + 16, CH - 54], fill=(NAVY2 if j == k else (200, 206, 222)) + (255,))
        draw_fn(dr); im.alpha_composite(L)
        fn = f"{base}-{k + 1}.jpg"; im.convert("RGB").save(fn, quality=92); files.append(fn)
    def ct(dr, y, txt, font, fill, sp=10):
        bb = dr.multiline_textbbox((0, 0), txt, font=font, spacing=sp, align="center")
        dr.multiline_text(((CW - (bb[2] - bb[0])) / 2, y), txt, font=font, fill=fill, spacing=sp, align="center")
    def navy_card(dr, y0, y1):
        dr.rounded_rectangle([60, y0 + 10, CW - 60, y1 + 10], 50, fill=(10, 14, 26, 255))
        dr.rounded_rectangle([60, y0, CW - 60, y1], 50, fill=NAVY2 + (255,), outline=GOLD + (255,), width=6)
    hook = spec.get("hook", "3 infos que\npersonne ne connaît")
    def p1(dr):
        navy_card(dr, 230, 1130)
        ct(dr, 320, "LE SAVAIS-TU ?", fit("LE SAVAIS-TU ?", "Bold", 110, CW - 200), GOLD + (255,))
        dr.rounded_rectangle([CW / 2 - 160, 470, CW / 2 + 160, 478], 4, fill=CYAN + (255,))
        hf = fit(hook, "Bold", 88, CW - 240); bb = dr.multiline_textbbox((0, 0), hook, font=hf, spacing=12, align="center")
        ct(dr, 720 - (bb[3] - bb[1]) / 2 - bb[1], hook, hf, WHITE + (255,), 12)
        pill = "3 infos  •  glisse  >"; pf = F("Bold", 52); pw = pf.getlength(pill) + 90
        dr.rounded_rectangle([(CW - pw) / 2, 960, (CW + pw) / 2, 1055], 48, fill=GOLD + (255,))
        dr.text((CW / 2, 1007), pill, font=pf, fill=NAVY + (255,), anchor="mm")
        ct(dr, 1170, "Enregistre ce post pour tes révisions", F("Medium", 44), NAVY2 + (255,))
    page(p1, spec.get("badge", "LE SAVAIS-TU ?"), 0)
    for k, info in enumerate(infos):
        def pk(dr, info=info, k=k):
            dr.rounded_rectangle([60, 190, CW - 60, 310], 36, fill=NAVY2 + (255,))
            dr.text((CW / 2, 250), f"Info {k + 1}/3", font=F("Bold", 64), fill=GOLD + (255,), anchor="mm")
            nl = len(info["lines"]); y_ex = 640 + nl * 120
            dr.rounded_rectangle([60, 350 + 8, CW - 60, y_ex + 250 + 8], 40, fill=NAVY2 + (255,))
            dr.rounded_rectangle([60, 350, CW - 60, y_ex + 250], 40, fill=(255, 255, 255, 255), outline=NAVY2 + (255,), width=5)
            tf = fit(info["title"], "Bold", 84, CW - 220); bb = dr.multiline_textbbox((0, 0), info["title"], font=tf, spacing=8, align="center")
            ct(dr, 470 - (bb[3] - bb[1]) / 2 - bb[1], info["title"], tf, INK_BLUE + (255,), 8)
            dr.line([(120, 590), (CW - 120, 590)], fill=(225, 228, 238, 255), width=3)
            for i, l in enumerate(info["lines"]):
                y = 630 + i * 120
                dr.ellipse([110, y + 6, 160, y + 56], fill=GOLD + (255,))
                dr.text((135, y + 31), str(i + 1), font=F("Bold", 32), fill=NAVY + (255,), anchor="mm")
                dr.multiline_text((190, y), l, font=fit(l, "Medium", 50, CW - 300), fill=INK + (255,), spacing=6)
            dr.rounded_rectangle([100, y_ex, CW - 100, y_ex + 210], 30, fill=GREEN + (50,), outline=GREEN + (255,), width=4)
            ct(dr, y_ex + 22, "Exemple", F("Medium", 38), (30, 120, 70, 255))
            ef = fit(info["example"], "Bold", 52, CW - 260); bb = dr.multiline_textbbox((0, 0), info["example"], font=ef, spacing=8, align="center")
            ct(dr, y_ex + 130 - (bb[3] - bb[1]) / 2 - bb[1], info["example"], ef, INK + (255,), 8)
        page(pk, info.get("badge", spec.get("badge", "")), k + 1)
    def p5(dr):
        navy_card(dr, 230, 1130)
        ct(dr, 330, "Abonne-toi !", fit("Abonne-toi !", "Bold", 120, CW - 200), GOLD + (255,))
        ct(dr, 500, "@revileague", F("Bold", 70), WHITE + (255,))
        ct(dr, 620, "Chaque jour : un quiz, des infos\nbrevet / bac et un défi", F("Medium", 48), (200, 206, 222, 255), 12)
        bw = 700; x0 = (CW - bw) / 2
        dr.rounded_rectangle([x0, 860, x0 + bw, 990], 65, fill=GOLD + (255,))
        dr.text((CW / 2, 925), "Rejoins la Ligue", font=F("Bold", 60), fill=NAVY + (255,), anchor="mm")
        ct(dr, 1020, "Lien en bio", F("Medium", 46), CYAN + (255,))
        ct(dr, 1170, "Révise comme dans un jeu, de la 6e à la Terminale", F("Medium", 40), NAVY2 + (255,))
    page(p5, spec.get("badge", "LE SAVAIS-TU ?"), 4)
    print("OK", " ".join(files)); return files

# ---------------------------------------------------------------- RENDU
def render(spec, out):
    check_glyphs(spec)
    if spec["type"] == "carrousel":
        return carrousel(spec, out)
    frame, sounds, T_END, *voices = {"quiz": quiz, "serie": serie, "astuce": astuce, "info": info}[spec["type"]](spec)
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
    _test_say()
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
