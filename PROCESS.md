# Réels RéviLeague : procédure de publication

Comptes : **@revileague** sur Instagram, TikTok et YouTube, publiés via le connecteur **Posty** (posty.social),
workspace `w0mwi8k5c9wzwfn7nbm` — Instagram `ch0mwi8pwc9tsrb5hu57`, TikTok `ch0mwi8n5lm0z3bno8dp`, YouTube `ch0mwi8mpd2pxpuvaji1`.
Secours Instagram : Windsor.ai for Social Media (connecteur `instagram`, compte `17841445183468796`).
Hébergement / archive des vidéos : GitHub Pages de ce dépôt → `https://corentirichard6264-coder.github.io/revileague/reels/<fichier>.mp4`.

RéviLeague est une plateforme de révision gamifiée (6e → Terminale) : cours interactifs, exercices adaptés au niveau,
corrections détaillées, XP, récompenses, rangs, classements entre joueurs. Ton : motivant, jeune, jamais condescendant.

## Les 3 créneaux (heure de Paris)

| Fenêtre | Format | Fichier | Spec `type` | Contenu |
|---|---|---|---|---|
| matin 7h – 11h59 | Quiz du jour | `reels/AAAA-MM-JJ-quiz.mp4` | `serie` | **8 questions** (6e à 3e), matières variées, countdown 4 s, xp 400. Durée ≈ 1 min 45 |
| midi 12h – 16h59 | Le savais-tu ? | `reels/AAAA-MM-JJ-astuce.mp4` | `astuce` | **5 infos** (règles / astuces / méthodes), chacune : titre + 2 lignes courtes + un exemple, matières et niveaux variés, xp 100. Durée ≈ 62 s |
| soir 17h – 22h59 | Défi de la Ligue | `reels/AAAA-MM-JJ-defi.mp4` | `serie` | **4 défis** plus durs (brevet, lycée, bac), badge de série « DÉFI • … », countdown 6 s, xp 400. Durée ≈ 1 min 10 |

**Heure de publication variable (demande de l'utilisateur, 20/11/2026) : jamais la même heure d'un jour à l'autre,
pour mesurer quel créneau donne le plus de vues.** Chaque routine tourne au début de sa fenêtre, prépare la vidéo,
puis la **programme** dans Posty (pas de publication immédiate) à une heure choisie ainsi :
1. Heures possibles = les heures pleines de la fenêtre (matin 7–11, midi 12–16, soir 17–22).
2. Dans `historique.json`, compte combien de fois chaque heure a déjà servi pour ce format (champ `heure_publication`).
   Garde les heures les moins utilisées, **exclus l'heure utilisée la veille** pour ce format, et tires-en une au hasard.
3. Minutes au hasard (00–59). L'heure finale doit être au moins 30 min après maintenant (sinon prends l'heure suivante).
4. Note dans `historique.json`, pour chaque entrée de la vidéo : `heure_publication` (ex. « 9 ») et
   `publie_a` (ex. « 2026-11-21T09:37:00+01:00 »). C'est ce qui servira à l'analyse des créneaux.

**Les 3 vidéos du jour durent plus d'une minute (61 s minimum, monétisation TikTok), avec voix off et musique de fond.**
Les séries peuvent dépasser 70 s si le format le demande (accord de l'utilisateur le 20/11/2026).

**Accroche (hook) — c'est elle qui décide si on reste sur TikTok.** Elle s'affiche en gros dès la 1re seconde
et la voix la lit : 2 lignes courtes maximum (`\n` entre les deux), un défi ou une promesse concrète, jamais une
description. Exemples : « 90 % des élèves se trompent\nà la question 3 », « Si tu as 5/5,\ntu as le niveau brevet »,
« Personne ne connaît la 4e\n(même les profs) », « 5 erreurs qui coûtent\ndes points au bac ». Varie l'accroche à chaque vidéo,
ne réutilise jamais la même deux fois de suite (vérifie historique.json), et varie aussi la 1re phrase de la légende.
La voix ne lit que la question (les réponses sont à l'écran) : garde les questions courtes.

**Ce qui fait percer les quiz TikTok (analyse vidIQ du 20/11/2026, quiz FR à 750 k – 950 k vues) :**
- aucune intro : la question 1 est à l'écran dès la 1re seconde, l'accroche affichée au-dessus (le générateur le fait) ;
- l'accroche est un **défi d'ego sur le score** : « Impossible d'avoir 5/5 », « Tu peux faire un sans-faute ? »,
  « Personne ne trouve la dernière » ; c'est ce format qui marche le mieux, privilégie-le ;
- la **question 1 est facile** (tout le monde doit pouvoir répondre, ça accroche), la difficulté monte, et la
  **dernière est la plus dure** (le générateur l'annonce : « Dernière question, la plus dure ! ») ;
- ~10-12 s par question, chrono 4 s avec tic-tac, réponse annoncée brièvement ;
- légende : finir par un appel à commenter précis, ex. « Écris GÉNIE en commentaire si tu as 5/5 🧠 » (varier le mot).

**Look des séries (20/11/2026, copié sur ces quiz)** : fond violet clair, carte blanche avec la question **et une image**,
**3 réponses** en gros boutons blancs empilés (A. B. C.), barre de temps, mauvaises réponses qui disparaissent, bonne
réponse en vert puis correction ; la voix annonce « Deuxième question… » et glisse « Like si tu as eu bon » (Q1) et
« Écris GÉNIE en commentaire… » (milieu). Le générateur fait tout ; la fin (score, XP, « Rejoins la Ligue ») ne change pas.
- **Mets 3 options par question** (4 possible mais moins lisible). Les options peuvent faire jusqu'à ~18 caractères.
- **Chaque question a une image** : `"image_query"` = 2-3 mots **en anglais**, concrets et visuels (« rome colosseum »,
  « human heart anatomy », « volcano eruption », « eiffel tower »). Le générateur cherche sur Openverse en domaine public /
  CC0 uniquement (aucun droit à payer, aucun crédit à citer). Tu peux aussi donner `"image"` = URL directe d'une image du
  domaine public (Wikimedia Commons). Pour une question abstraite (grammaire, calcul), choisis un objet lié au sujet
  (« open book », « calculator », « blackboard math »).
- **Vérifie chaque image** sur les images extraites (une par question) : si elle est hors sujet, moche, ou montre une
  personne reconnaissable, une marque ou un logo, change `image_query` et relance ; si rien ne va, retire `image_query`
  (la carte s'affiche sans image).

Le générateur refuse une `serie` ou une `astuce` de moins de 61 s (il faut dépasser 1 min pour la monétisation TikTok) : ajouter une question / une info dans ce cas.
La musique de fond est une boucle originale synthétisée par le générateur (libre de droits, aucun son à ajouter
dans TikTok/Instagram). La voix off (Fish Audio) lit l'intro, chaque question ou info, et la fin : si le script affiche
« Voix off : non », la vidéo ne respecte pas la consigne → le signaler dans la notification.
Alterner les matières (maths, français, histoire-géo, SVT, physique-chimie, anglais, philo en Terminale) et les niveaux,
y compris à l'intérieur d'une série. Ne jamais répéter une question déjà présente dans `historique.json`.

## Étapes d'une publication

1. Lire `historique.json` pour éviter les doublons.
2. Écrire la spec JSON (voir l'en-tête de `generateur/make_reel.py`). Règles :
   - contenu **exact et vérifié** (une seule bonne réponse, distracteurs plausibles) ;
   - textes courts : options ≤ 18 caractères, lignes ≤ 30 caractères, `\n` pour couper ;
   - caractères interdits par la police : ⁴ ⁵ ᵉ → (écrire « 4e », « puissance 5 », « donc ») ; le script refuse sinon ;
   - pas d'emoji dans la vidéo ; aucun personnage, marque ou œuvre protégée.
   - **voix off** (séries et astuces) : lue par Fish Audio si `FISH_API_KEY` est définie dans l'environnement. Quand l'écrit
     se lit mal (puissances, fractions, sigles, dates), ajouter `dit_question` / `dit_explication` à la question
     (ou `dit` à une info d'astuce) avec la phrase à prononcer (ex. « 2 puissance 3 fois 2 puissance 2 ? A : 10. B : 32. C : 64. D : 12. »).
3. `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-<quiz|astuce|defi>.mp4`, puis extraire des images
   avec ffmpeg (la 1re image = couverture automatique, puis une par question / info) et les regarder.
   Le script affiche « Voix off : oui/non » : si c'est « non » ou si Fish Audio échoue, le signaler dans le message final.
4. Choisir l'heure de publication (règle « Heure de publication variable » ci-dessus).
5. Commit + push sur `main` (vidéo + ajout à `historique.json`, une entrée par question / info, avec `heure_publication`
   et `publie_a`).
6. **Programmer** via Posty : `create_media_upload` → PUT du fichier sur `uploadUrl` avec tous les `uploadHeaders` →
   `complete_media_upload` → `create_post` (3 contenus, **`scheduledAt` = l'heure choisie**, ISO avec le décalage
   de Paris, ex. `2026-11-21T09:37:00+01:00`) → `act_on_post` submit (skipApproval) → `act_on_post` publish **at: scheduled**
   → `get_post` doit montrer le post programmé à la bonne heure. TikTok : metadata `privacyLevel: PUBLIC_TO_EVERYONE`.
   YouTube : metadata `title` (≤ 100 caractères), description avec le lien du site et #shorts.
7. Légende Instagram / TikTok : 1 phrase d'accroche + appel à commenter (« Ton score ? ») + « Révise comme dans un jeu
   sur RéviLeague 🏆 (lien en bio) » + 5 à 8 hashtags pertinents (#revisions #brevet #bac #college #lycee + matières).
8. **Contrôle de la publication précédente** : chaque routine relit avec `get_post` le post programmé par la routine
   d'avant (dernier `posty_post_id` de `historique.json`) et note dans l'historique le statut par réseau. Si Instagram a
   échoué : publier en secours avec Windsor `execute_action` (`create_video_post`, params
   `{video_url, caption, share_to_feed: true}`) à partir de l'URL GitHub Pages (vérifiée avec WebFetch). Commit + push.

En cas d'échec (publication refusée, accès GitHub/Posty perdu) : ne pas réessayer en boucle, notifier l'utilisateur avec la cause.
