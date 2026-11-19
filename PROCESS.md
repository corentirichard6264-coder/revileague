# Réels RéviLeague : procédure de publication

Comptes : **@revileague** sur Instagram, TikTok et YouTube, publiés via le connecteur **Posty** (posty.social),
workspace `w0mwi8k5c9wzwfn7nbm` — Instagram `ch0mwi8pwc9tsrb5hu57`, TikTok `ch0mwi8n5lm0z3bno8dp`, YouTube `ch0mwi8mpd2pxpuvaji1`.
Secours Instagram : Windsor.ai for Social Media (connecteur `instagram`, compte `17841445183468796`).
Hébergement / archive des vidéos : GitHub Pages de ce dépôt → `https://corentirichard6264-coder.github.io/revileague/reels/<fichier>.mp4`.

RéviLeague est une plateforme de révision gamifiée (6e → Terminale) : cours interactifs, exercices adaptés au niveau,
corrections détaillées, XP, récompenses, rangs, classements entre joueurs. Ton : motivant, jeune, jamais condescendant.

## Les 3 créneaux (heure de Paris)

| Heure | Format | Spec `type` | Contenu |
|---|---|---|---|
| 8h | Question du jour | `serie` | **5 questions** rapides (6e à 3e), matières variées, countdown 4 s, xp 250. Durée ≈ 65 s |
| 13h | Le savais-tu ? | `astuce` | **5 infos** (règles / astuces / méthodes), chacune : titre + 2 lignes courtes + un exemple, matières et niveaux variés, xp 100. Durée ≈ 62 s |
| 20h | Défi de la Ligue | `serie` | **4 défis** plus durs (brevet, lycée, bac), badge de série « DÉFI • … », countdown 6 s, xp 400. Durée ≈ 63 s |

**Les 3 vidéos du jour durent un peu plus d'une minute (pas plus de ~70 s), avec voix off et musique de fond**
(demande de l'utilisateur, 16/11/2026 ; raccourcies le 19/11 car 2 min faisait décrocher sur TikTok).

**Accroche (hook) — c'est elle qui décide si on reste sur TikTok.** Elle s'affiche en gros dès la 1re seconde
et la voix la lit : 2 lignes courtes maximum (`\n` entre les deux), un défi ou une promesse concrète, jamais une
description. Exemples : « 90 % des élèves se trompent\nà la question 3 », « Si tu as 5/5,\ntu as le niveau brevet »,
« Personne ne connaît la 4e\n(même les profs) », « 5 erreurs qui coûtent\ndes points au bac ». Varie l'accroche à chaque vidéo,
ne réutilise jamais la même deux fois de suite (vérifie historique.json), et varie aussi la 1re phrase de la légende.
La voix ne lit que la question (les réponses sont à l'écran) : garde les questions courtes.

Le générateur refuse une `serie` ou une `astuce` de moins de 60 s : ajouter une question / une info dans ce cas.
La musique de fond est une boucle originale synthétisée par le générateur (libre de droits, aucun son à ajouter
dans TikTok/Instagram). La voix off (Fish Audio) lit l'intro, chaque question ou info, et la fin : si le script affiche
« Voix off : non », la vidéo ne respecte pas la consigne → le signaler dans la notification.
Alterner les matières (maths, français, histoire-géo, SVT, physique-chimie, anglais, philo en Terminale) et les niveaux,
y compris à l'intérieur d'une série. Ne jamais répéter une question déjà présente dans `historique.json`.

## Étapes d'une publication

1. Lire `historique.json` pour éviter les doublons.
2. Écrire la spec JSON (voir l'en-tête de `generateur/make_reel.py`). Règles :
   - contenu **exact et vérifié** (une seule bonne réponse, distracteurs plausibles) ;
   - textes courts : options ≤ 10 caractères si possible, lignes ≤ 30 caractères, `\n` pour couper ;
   - caractères interdits par la police : ⁴ ⁵ ᵉ → (écrire « 4e », « puissance 5 », « donc ») ; le script refuse sinon ;
   - pas d'emoji dans la vidéo ; aucun personnage, marque ou œuvre protégée.
   - **voix off** (séries et astuces) : lue par Fish Audio si `FISH_API_KEY` est définie dans l'environnement. Quand l'écrit
     se lit mal (puissances, fractions, sigles, dates), ajouter `dit_question` / `dit_explication` à la question
     (ou `dit` à une info d'astuce) avec la phrase à prononcer (ex. « 2 puissance 3 fois 2 puissance 2 ? A : 10. B : 32. C : 64. D : 12. »).
3. `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-HHh.mp4`, puis extraire 3-4 images avec ffmpeg
   La 1re image de la vidéo est une couverture automatique (miniature Instagram / TikTok) : vérifie-la aussi.
   (dont une par question pour une série) et les regarder. Le script affiche « Voix off : oui/non » :
   si c'est « non » ou si Fish Audio échoue, le signaler dans le message final (la vidéo reste publiable sans voix).
4. Commit + push sur `main` (vidéo + ajout à `historique.json`, une entrée par question pour une série).
5. Publier via Posty : `create_media_upload` → PUT du fichier sur `uploadUrl` avec tous les `uploadHeaders` →
   `complete_media_upload` → `create_post` (3 contenus) → `act_on_post` submit (skipApproval) → `act_on_post` publish now
   → `get_post` jusqu'à `deliveryStatus: delivered`. TikTok : metadata `privacyLevel: PUBLIC_TO_EVERYONE`.
   YouTube : metadata `title` (≤ 100 caractères), description avec le lien du site et #shorts.
6. Légende Instagram / TikTok : 1 phrase d'accroche + appel à commenter (« Ton score ? ») + « Révise comme dans un jeu
   sur RéviLeague 🏆 (lien en bio) » + 5 à 8 hashtags pertinents (#revisions #brevet #bac #college #lycee + matières).
7. Si Instagram échoue via Posty : publier en secours avec Windsor `execute_action` (`create_video_post`,
   params `{video_url, caption, share_to_feed: true}`) à partir de l'URL GitHub Pages (vérifiée avec WebFetch).
8. Compléter `historique.json` (id du post Posty, statut/lien par réseau), commit + push.

En cas d'échec (publication refusée, accès GitHub/Posty perdu) : ne pas réessayer en boucle, notifier l'utilisateur avec la cause.
