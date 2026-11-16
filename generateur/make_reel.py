"""Générateur de réels RéviLeague (1080x1920, 30 fps, son synthétique).

Usage : python3 make_reel.py spec.json sortie.mp4

Trois formats de spec JSON :
  quiz   : {"type":"quiz","badge":"4e • MATHS","hook":"Tu peux répondre\\nen 5 secondes ?",
            "question":"2³ × 2² = ?","options":["10","32","64","12"],"answer":1,
            "explain":"On additionne les exposants :\\n3 + 2 = 5, donc 2 puissance 5 = 32",
            "xp":50,"countdown":5}
  serie  : {"type":"serie","badge":"COLLÈGE • MIX","hook":"5 questions.\\nTu fais combien ?","countdown":5,"xp":250,
            "questions":[{"badge":"4e • MATHS","question":...,"options":[...],"answer":1,"explain":...}, ...]}
           Vidéo d'au moins 60 s (le script refuse sinon) : 5 questions avec countdown 5, 4 avec countdown 7.
           Voix off Fish Audio si la variable d'environnement FISH_API_KEY existe (FISH_VOICE_ID = voix choisie) :
           elle lit l'intro, chaque question + ses 4 réponses, la correction, le score et la fin ; le chrono
           démarre après la lecture. Par question, "dit_question" / "dit_explication" (optionnels) remplacent
           le texte lu quand l'écrit se lit mal (ex. "2³ × 2²" -> "2 puissance 3 fois 2 puissance 2").
  astuce : {"type":"astuce","badge":"3e • FRANÇAIS","title":"Participe passé\\navec avoir",
            "lines":["S'accorde avec le COD...","...seulement s'il est placé AVANT"],
            "example":"Les pommes que j'ai mangées","xp":20}
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
        p = FD + f"Poppins-{style}.ttf"
        _cache[k] = ImageFont.truetype(p if os.path.exists(p) else FALLBACK, size)
    return _cache[k]

NAVY = (15, 20, 32); NAVY2 = (28, 36, 60); CARD = (34, 44, 72)
GOLD = (255, 196, 61); CYAN = (64, 214, 255); GREEN = (52, 211, 120)
RED = (255, 92, 108); WHITE = (245, 247, 255); GREY = (150, 160, 190)

def check_glyphs(spec):
    try:
        from fontTools.ttLib import TTFont
        p = FD + "Poppins-Bold.ttf"
        cmap = TTFont(p if os.path.exists(p) else FALLBACK).getBestCmap()
    except Exception:
        return
    txt = json.dumps(spec, ensure_ascii=False)
    bad = sorted({c for c in txt if ord(c) > 127 and ord(c) not in cmap})
    if bad:
        sys.exit("Caractères non supportés par la police, à réécrire : " + " ".join(bad))

def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def prog(t, a, d): return ease((t - a) / d)

def make_bg():
    bg = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(NAVY[i] + (NAVY2[i] - NAVY[i]) * k) for i in range(3)))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse([-300, -200, 700, 700], fill=(40, 60, 120)); gd.ellipse([500, 1300, 1400, 2200], fill=(70, 50, 110))
    bg = Image.blend(bg, ImageChops.lighter(bg, glow.filter(ImageFilter.GaussianBlur(180))), 0.7)
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
        a = prog(t, T_Q, 0.5) * (1 - prog(t, T_OUT - 0.4, 0.4))
        def qd(dr):
            dr.rounded_rectangle([90, 560, W - 90, 820], 40, fill=CARD + (255,), outline=(70, 85, 130, 255), width=4)
            bb = dr.multiline_textbbox((0, 0), q["question"], font=qf, align="center")
            ctext(dr, 690 - (bb[3] - bb[1]) / 2 - bb[1], q["question"], qf, GOLD + (255,))
        im.alpha_composite(layer(qd, a))
    if T_OPT <= t < T_OUT:
        for i, opt in enumerate(q["options"]):
            good = i == q["answer"]
            ap = prog(t, T_OPT + i * 0.12, 0.35) * (1 if good else 1 - prog(t, T_DIM - 0.3, 0.4)) * (1 - prog(t, T_OUT - 0.4, 0.4))
            if ap <= 0: continue
            x0 = 90 + (i % 2) * 470; y0 = 900 + (i // 2) * 230 + 30 * (1 - prog(t, T_OPT + i * 0.12, 0.35))
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
            cx, cy, r = W // 2, 1490, 105
            dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CARD + (255,))
            dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=(GOLD if rem > 2 else RED) + (255,), width=16)
            dr.text((cx, cy), str(math.ceil(rem)), font=F("Bold", 100), fill=WHITE + (255,), anchor="mm")
            ctext(dr, 1625, "Mets ta réponse en commentaire", F("Medium", 44), GREY + (255,))
        im.alpha_composite(layer(c, a))
    if T_REVEAL + 0.3 <= t < T_OUT:
        a = prog(t, T_REVEAL + 0.3, 0.4) * (1 - prog(t, T_OUT - 0.4, 0.4))
        def e(dr):
            dr.rounded_rectangle([90, 1400, W - 90, 1640], 36, fill=(255, 255, 255, 22))
            bb = dr.multiline_textbbox((0, 0), q["explain"], font=ef, spacing=14, align="center")
            ctext(dr, 1520 - (bb[3] - bb[1]) / 2 - bb[1], q["explain"], ef, WHITE + (255,), 14)
        im.alpha_composite(layer(e, a))

def q_sounds(T_COUNT, cd):
    s = [(T_COUNT + k, 0.12, 1200 if k < cd - 1 else 900, 0.35, 40) for k in range(cd)]
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
    body = {"text": text, "format": "mp3", "mp3_bitrate": 128, "language": "fr", "prosody": {"speed": 1.05}}
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

# ---------------------------------------------------------------- SÉRIE (plusieurs questions, >= 60 s)
MIN_SERIE = 60.0

def serie(spec):
    qs = spec["questions"]; cd = spec.get("countdown", 5); n = len(qs)
    # voix off : intro, chaque question + réponses, chaque correction, score, fin
    v_intro = tts(say(spec["hook"]))
    def lire_q(q):
        txt = say(q["question"]); txt += "" if txt[-1:] in ".?!" else "."
        return txt + " " + ". ".join(f"{'ABCD'[i]} : {say(o)}" for i, o in enumerate(q["options"])) + "."
    v_q = [tts(q.get("dit_question") or lire_q(q)) for q in qs]
    v_e = [tts(q.get("dit_explication") or say(f"Réponse {'ABCD'[q['answer']]} : {q['options'][q['answer']]}. {q['explain']}")) for q in qs]
    v_score = tts(f"Alors, ton score sur {n} ? Dis-le en commentaire !")
    v_cta = tts("Révise comme dans un jeu. Rejoins la Ligue, lien en bio !")
    print("Voix off :", "oui" if v_intro else "non (FISH_API_KEY absente)")

    T_INTRO = max(2.4, 0.3 + dur(v_intro) + 0.4)
    # par question : réponses à 0,7 s, chrono après la lecture, correction lue, sortie 0,4 s
    T_CNT = [max(1.4, 0.3 + dur(v) + 0.3) for v in v_q]
    SEG = [c + cd + max(3.6, 0.4 + dur(v) + 0.6) + 0.4 for c, v in zip(T_CNT, v_e)]
    S = [T_INTRO + sum(SEG[:k]) for k in range(n)]
    T_SCORE = T_INTRO + sum(SEG); T_XP = T_SCORE + max(3.0, 0.2 + dur(v_score) + 0.3); T_CTA = T_XP + 2.4
    T_END = T_CTA + max(3.0, 0.3 + dur(v_cta) + 0.4)
    if T_END < MIN_SERIE:
        sys.exit(f"Série trop courte ({T_END:.1f} s < {MIN_SERIE:.0f} s) : ajoute une question.")
    hookf = fit(spec["hook"], "Bold", 84, W - 160)
    fonts = [q_fonts(q) for q in qs]

    def frame(t, bg):
        im = bg.copy().convert("RGBA")
        k = max([0] + [j for j in range(n) if S[j] <= t])
        header(im, qs[k].get("badge", spec["badge"]) if T_INTRO <= t < T_SCORE else spec["badge"])
        if t < T_INTRO:
            a = prog(t, 0, 0.5) * (1 - prog(t, T_INTRO - 0.4, 0.4))
            im.alpha_composite(layer(lambda dr: ctext(dr, 700 + 40 * (1 - prog(t, 0, 0.5)), spec["hook"], hookf, WHITE + (255,), 4), a))
        elif t < T_SCORE:
            u = t - S[k]
            a = prog(u, 0, 0.4) * (1 - prog(u, SEG[k] - 0.4, 0.4))
            def pr(dr):
                ctext(dr, 260, f"Question {k + 1}/{n}", F("Bold", 64), CYAN + (255,))
                x0 = (W - (n * 44 - 16)) / 2
                for j in range(n):
                    dr.rounded_rectangle([x0 + j * 44, 380, x0 + j * 44 + 28, 396], 8,
                                         fill=GOLD + (255,) if j <= k else (255, 255, 255, 40))
            im.alpha_composite(layer(pr, a))
            draw_question(im, u, qs[k], fonts[k], cd, 0.0, 0.7, T_CNT[k], T_CNT[k] + cd + 1.2, SEG[k])
        elif t < T_CTA:
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
    voices += [(S[k] + 0.3, v_q[k]) for k in range(n)] + [(S[k] + T_CNT[k] + cd + 0.4, v_e[k]) for k in range(n)]
    return frame, sounds, T_END, [(s, c) for s, c in voices if c]

# ---------------------------------------------------------------- ASTUCE
def astuce(spec):
    lines = spec["lines"]
    T_TITLE = 1.4; T_L0 = 2.6; STEP = 1.4
    T_EX = T_L0 + STEP * len(lines) + 0.2
    T_XP = T_EX + 2.6; T_CTA = T_XP + 2.0; T_END = T_CTA + 2.8
    tf = fit(spec["title"], "Bold", 92, W - 260)
    lf = [fit(l, "Medium", 50, W - 300) for l in lines]
    exf = fit(spec["example"], "Bold", 54, W - 260)

    def frame(t, bg):
        im = bg.copy().convert("RGBA"); header(im, spec["badge"])
        if t < T_CTA:
            a = prog(t, 0, 0.5) * (1 - prog(t, T_CTA - 0.4, 0.4))
            y = 700 - 440 * prog(t, T_TITLE, 0.5)
            im.alpha_composite(layer(lambda dr: ctext(dr, y, "Le savais-tu ?", F("Bold", 90), CYAN + (255,)), a))
        if T_TITLE <= t < T_CTA:
            a = prog(t, T_TITLE, 0.5) * (1 - prog(t, T_CTA - 0.4, 0.4))
            def td(dr):
                dr.rounded_rectangle([90, 420, W - 90, 680], 40, fill=CARD + (255,), outline=(70, 85, 130, 255), width=4)
                bb = dr.multiline_textbbox((0, 0), spec["title"], font=tf, spacing=6, align="center")
                ctext(dr, 550 - (bb[3] - bb[1]) / 2 - bb[1], spec["title"], tf, GOLD + (255,), 6)
            im.alpha_composite(layer(td, a))
        for i, l in enumerate(lines):
            t0 = T_L0 + i * STEP
            if t0 <= t < T_CTA:
                p = prog(t, t0, 0.45); a = p * (1 - prog(t, T_CTA - 0.4, 0.4))
                y = 760 + i * 150 + 30 * (1 - p)
                def ld(dr, l=l, y=y, f=lf[i]):
                    dr.ellipse([110, y + 22, 150, y + 62], fill=GOLD + (255,))
                    dr.text((130, y + 42), str(i + 1), font=F("Bold", 28), fill=NAVY + (255,), anchor="mm")
                    dr.multiline_text((180, y + 6), l, font=f, fill=WHITE + (255,), spacing=6)
                im.alpha_composite(layer(ld, a))
        if T_EX <= t < T_CTA:
            p = prog(t, T_EX, 0.45); a = p * (1 - prog(t, T_CTA - 0.4, 0.4))
            y0 = 790 + len(lines) * 150
            def ed(dr):
                dr.rounded_rectangle([90, y0, W - 90, y0 + 220], 36, fill=GREEN + (60,), outline=GREEN + (255,), width=4)
                ctext(dr, y0 + 22, "Exemple", F("Medium", 40), (180, 255, 210, 255))
                bb = dr.multiline_textbbox((0, 0), spec["example"], font=exf, spacing=8, align="center")
                ctext(dr, y0 + 140 - (bb[3] - bb[1]) / 2 - bb[1], spec["example"], exf, WHITE + (255,), 8)
            im.alpha_composite(layer(ed, a))
        if T_XP <= t < T_CTA: xp_block(im, t, T_XP, T_CTA, spec.get("xp", 20), y=1650)
        if t >= T_CTA: cta(im, t, T_CTA)
        return im.convert("RGB")

    sounds = [(T_TITLE, 0.4, 700, 0.3, 8)] + [(T_L0 + i * STEP, 0.15, 1000, 0.25, 30) for i in range(len(lines))]
    sounds += [(T_EX, 0.6, 880, 0.3, 5), (T_EX + 0.08, 0.6, 1320, 0.25, 5)]
    sounds += [(T_XP + j * 0.07, 0.25, fq, 0.25, 12) for j, fq in enumerate([660, 880, 1100, 1320])]
    return frame, sounds, T_END

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
    for start, dur, freq, vol, decay in sounds:
        for k in range(int(dur * SR)):
            i = int(start * SR) + k
            if i >= N: break
            tt = k / SR; buf[i] += vol * math.sin(2 * math.pi * freq * tt) * math.exp(-decay * tt)
    for i in range(N):
        tt = i / SR; buf[i] += 0.04 * math.sin(2 * math.pi * 110 * tt) * (0.6 + 0.4 * math.sin(math.pi * tt))
    wav = out + ".wav"
    with wave.open(wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 30000)) for v in buf))
    bg = make_bg()
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out],
                         stdin=subprocess.PIPE)
    for n in range(int(T_END * FPS)):
        p.stdin.write(frame(n / FPS, bg).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    if p.returncode: sys.exit("ffmpeg a échoué")
    print("OK", out, f"{T_END:.1f}s")

if __name__ == "__main__":
    render(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
