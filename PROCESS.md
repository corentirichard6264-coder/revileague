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
| 8h | Question du jour | `serie` | **5 questions** rapides (6e à 3e), matières variées, countdown 5 s, xp 250, hook « 5 questions.\nTu fais combien ? » ou variante. Durée ≥ 60 s |
| 13h | Le savais-tu ? | `astuce` | Règle / astuce / méthode à retenir : 2 à 3 lignes courtes + un exemple, xp 20 |
| 20h | Défi de la Ligue | `serie` | **4 défis** plus durs (brevet, lycée, bac), badge de série « DÉFI • … », countdown 7 s, xp 400. Durée ≥ 60 s |

Le générateur refuse une `serie` de moins de 60 s : ajouter une question dans ce cas.
Alterner les matières (maths, français, histoire-géo, SVT, physique-chimie, anglais, philo en Terminale) et les niveaux,
y compris à l'intérieur d'une série. Ne jamais répéter une question déjà présente dans `historique.json`.

## Étapes d'une publication

1. Lire `historique.json` pour éviter les doublons.
2. Écrire la spec JSON (voir l'en-tête de `generateur/make_reel.py`). Règles :
   - contenu **exact et vérifié** (une seule bonne réponse, distracteurs plausibles) ;
   - textes courts : options ≤ 10 caractères si possible, lignes ≤ 30 caractères, `\n` pour couper ;
   - caractères interdits par la police : ⁴ ⁵ ᵉ → (écrire « 4e », « puissance 5 », « donc ») ; le script refuse sinon ;
   - pas d'emoji dans la vidéo ; aucun personnage, marque ou œuvre protégée.
3. `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-HHh.mp4`, puis extraire 3-4 images avec ffmpeg
   (dont une par question pour une série) et les regarder.
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
