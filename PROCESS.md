# Réels RéviLeague : procédure de publication

Compte Instagram : **@revileague** (Windsor.ai for Social Media, connecteur `instagram`, compte `17841445183468796`).
Hébergement des vidéos : GitHub Pages de ce dépôt → `https://corentirichard6264-coder.github.io/revileague/reels/<fichier>.mp4`.

RéviLeague est une plateforme de révision gamifiée (6e → Terminale) : cours interactifs, exercices adaptés au niveau,
corrections détaillées, XP, récompenses, rangs, classements entre joueurs. Ton : motivant, jeune, jamais condescendant.

## Les 3 créneaux (heure de Paris)

| Heure | Format | Spec `type` | Contenu |
|---|---|---|---|
| 8h | Question du jour | `quiz` | Question rapide, niveau 6e à 3e surtout, countdown 5 s, xp 50, hook « Tu peux répondre\nen 5 secondes ? » ou variante |
| 13h | Le savais-tu ? | `astuce` | Règle / astuce / méthode à retenir : 2 à 3 lignes courtes + un exemple, xp 20 |
| 20h | Défi de la Ligue | `quiz` | Question plus dure (niveau brevet, lycée, bac), badge « DÉFI • … », countdown 7 s, xp 100 |

Alterner les matières (maths, français, histoire-géo, SVT, physique-chimie, anglais, philo en Terminale) et les niveaux.
Ne jamais répéter un sujet déjà présent dans `historique.json`.

## Étapes d'une publication

1. Lire `historique.json` pour éviter les doublons.
2. Écrire la spec JSON (voir l'en-tête de `generateur/make_reel.py`). Règles :
   - contenu **exact et vérifié** (une seule bonne réponse, distracteurs plausibles) ;
   - textes courts : options ≤ 12 caractères si possible, lignes ≤ 30 caractères, `\n` pour couper ;
   - caractères interdits par la police : ⁴ ⁵ ᵉ → (écrire « 4e », « puissance 5 », « donc ») ; le script refuse sinon ;
   - pas d'emoji dans la vidéo ; aucun personnage, marque ou œuvre protégée.
3. `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-HHh.mp4`, puis extraire 2-3 images avec ffmpeg et les regarder.
4. Commit + push sur `main` (vidéo + ajout à `historique.json`).
5. Attendre ~2 min que GitHub Pages se mette à jour, puis vérifier l'URL avec WebFetch (doit renvoyer du binaire, pas une 404).
6. Publier : Windsor `execute_action`, connecteur `instagram`, action `create_video_post`,
   compte `17841445183468796`, params `{video_url, caption, share_to_feed: true}`.
7. Légende : 1 phrase d'accroche + appel à commenter + « Révise comme dans un jeu sur RéviLeague 🏆 (lien en bio) »
   + 5 à 8 hashtags pertinents (#revisions #brevet #bac #college #lycee + matière). Max 2200 caractères.
8. Compléter l'entrée dans `historique.json` avec le `media_id`, commit + push.

En cas d'échec (publication refusée, URL en 404 après 5 min, accès GitHub/Windsor perdu) : ne pas réessayer en boucle,
notifier l'utilisateur avec la cause.
