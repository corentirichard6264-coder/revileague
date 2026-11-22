# Réels RéviLeague : procédure de publication

Comptes : **@revileague** sur Instagram, TikTok et YouTube, publiés via le connecteur **Posty** (posty.social),
workspace `w0mwi8k5c9wzwfn7nbm` — Instagram `ch0mwi8pwc9tsrb5hu57`, TikTok `ch0mwi8n5lm0z3bno8dp`, YouTube `ch0mwi8mpd2pxpuvaji1`.
Secours Instagram : Windsor.ai for Social Media (connecteur `instagram`, compte `17841445183468796`).
Hébergement / archive des vidéos : GitHub Pages de ce dépôt → `https://corentirichard6264-coder.github.io/revileague/reels/<fichier>.mp4`.

RéviLeague est une plateforme de révision gamifiée (6e → Terminale) : cours interactifs, exercices adaptés au niveau,
corrections détaillées, XP, récompenses, rangs, classements entre joueurs. Ton : motivant, jeune, jamais condescendant.

## Les 4 publications du jour (heure de Paris)

| Fenêtre | Routine lancée à | Format | Fichier | Spec `type` | Contenu |
|---|---|---|---|---|---|
| 7h – 9h59 | 6h00 | Quiz du jour | `reels/AAAA-MM-JJ-quiz.mp4` | `serie` | **8 questions** (6e à 3e), matières variées, countdown 4 s, xp 400. Durée ≈ 1 min 45 |
| 10h – 13h59 | 9h15 | **Info actu** (news éducation, dates, événements) | `reels/AAAA-MM-JJ-actu.mp4` | `info` | **Une actu ou une date à venir** utile aux élèves, en tableau de 5-6 lignes + conseil + source officielle (voir « Format Info actu »). xp 100. ≥ 61 s |
| 14h – 17h59 | 13h15 | **Le savais-tu ?** en **carrousel photo** (pas une vidéo) | `reels/AAAA-MM-JJ-savais-1.jpg` … `-5.jpg` | `carrousel` | 5 images : couverture « Le savais-tu ? », **3 infos** (règles / astuces / méthodes, matières et niveaux variés), « Abonne-toi ! » |
| 18h – 22h59 | 17h15 | Défi de la Ligue | `reels/AAAA-MM-JJ-defi.mp4` | `serie` | **4 défis** plus durs (brevet, lycée, bac), badge de série « DÉFI • … », countdown 6 s, xp 400. Durée ≈ 1 min 10 |

**Heure de publication variable (demande de l'utilisateur, 20/11/2026) : jamais la même heure d'un jour à l'autre,
pour mesurer quel créneau donne le plus de vues.** Chaque routine tourne au début de sa fenêtre, prépare la vidéo,
puis la **programme** dans Posty (pas de publication immédiate) à une heure choisie ainsi :
1. Heures possibles = les heures pleines de la fenêtre (quiz 7–9, actu 10–13, savais-tu 14–17, défi 18–22).
2. Dans `historique.json`, compte combien de fois chaque heure a déjà servi pour ce format (champ `heure_publication`).
   Garde les heures les moins utilisées, **exclus l'heure utilisée la veille** pour ce format, et tires-en une au hasard.
3. Minutes au hasard (00–59). L'heure finale doit être au moins 30 min après maintenant (sinon prends l'heure suivante).
4. Note dans `historique.json`, pour chaque entrée de la vidéo : `heure_publication` (ex. « 9 ») et
   `publie_a` (ex. « 2026-11-21T09:37:00+01:00 »). C'est ce qui servira à l'analyse des créneaux.

**Les 4 vidéos du jour durent plus d'une minute (61 s minimum, monétisation TikTok), avec voix off et musique de fond.**
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

**Format « Info brevet / bac » (`type: "info"`, ajouté le 20/11/2026, inspiré des comptes d'infos brevet très enregistrés)**
- Sujet : une info **officielle et utile** pour les élèves : calcul des points et mentions du brevet, dates d'examen,
  épreuves et coefficients, oral, contrôle continu du bac, bac de français, Grand oral, Parcoursup / Affelnet (dates,
  étapes), passage en seconde, redoublement… Alterner brevet (3e) et lycée/bac. Jamais deux fois le même sujet de suite.
- **Exactitude obligatoire** : chaque chiffre et chaque date vient d'une source officielle consultée pendant la routine
  (education.gouv.fr, eduscol.education.gouv.fr, service-public.fr, parcoursup.fr, onisep.fr), pour la **session en
  cours** (2027 en 2026-2027). Si tu ne trouves pas de source officielle claire, **change de sujet**. Mets la source
  dans `source` (ex. « education.gouv.fr (BO 2026) »). Aucune rumeur, aucune réforme non publiée.
- Spec : `{"type":"info","badge":"3e • BREVET","hook":"Brevet 2027 :
ta moyenne de 3e
compte pour 40 %","stamp":"OFFICIEL",
  "table_title":"brevet 2027","table_tag":"ta note finale","rows":[{"label":"examens","value":"60 % de la note","dit":"..."}, ...],
  "conseil":"Chaque contrôle de 3e compte :
ne lâche rien dès maintenant","dit_conseil":"...","source":"education.gouv.fr (BO 2026)",
  "question":"Tu le savais ?","xp":100}`
  - `hook` : 3 lignes courtes max, la 1re (en or) annonce l'examen (« Brevet 2027 : », « Bac 2027 : », « Parcoursup : »),
    puis l'info choc. `stamp` : « OFFICIEL », « NOUVEAU », « IMPORTANT » ou « DATES ».
  - `rows` : **5 ou 6 lignes** ; `label` ≤ 12 caractères, `value` ≤ 20 caractères (court, percutant).
  - **Durée ≥ 61 s** : la voix lit l'accroche, chaque ligne puis le conseil. Donne à chaque ligne un `dit` de 1-2 phrases
    qui explique (ex. « Les épreuves finales, c'est 60 % de ta note : français, maths, sciences, histoire-géo et l'oral. »)
    et un `dit_conseil` de 2-3 phrases. Si le script dit « trop courte », allonge les `dit`.
- Légende : 1 phrase choc + **« (garde-la) »** + « Révise comme dans un jeu sur RéviLeague 🏆 (lien en bio) » +
  hashtags dont **l'année de naissance du public** (#2012 pour les 3e de 2026-2027, #2010 pour les 1re, #2009 pour les
  Terminales) + #brevet2027 / #bac2027 + #3eme / #lycee.

**Format « Info actu » (`type: "info"`, routine de 9h15, publication 10h–14h, ajouté le 22/11/2026)** — même rendu que l'Info
brevet / bac, mais centré sur **l'actualité et le calendrier** (demande de l'utilisateur : « des news, des dates, des
événements qui peuvent servir et intéresser les élèves », car la vidéo « Bac 2027 : toutes les dates » a fait
x14 la portée habituelle avec 57 partages et 40 enregistrements sur Instagram).
- **Chaque jour, cherche** (WebSearch / WebFetch) ce qui est nouveau ou proche, dans cet ordre :
  1. **Actus des 7 derniers jours** : annonces du ministère, réformes publiées, nouveaux textes au BO, changements
     d'examens, résultats de concours ou classements officiels (education.gouv.fr/actualites, service-public.fr/actualites,
     eduscol, onisep.fr, parcoursup.fr, etudiant.gouv.fr).
  2. **Dates à venir dans les 30 prochains jours** : vacances scolaires (par zone), ouverture/clôture Parcoursup,
     journées portes ouvertes, salons de l'orientation, inscriptions aux examens, brevets/bacs blancs habituels,
     concours (Kangourou, Olympiades…), Journée nationale…
  3. **Calendriers officiels utiles** à rappeler (examens 2027, Parcoursup 2027, vacances 2026-2027), en variant
     l'angle (« dans 3 semaines : … », « ce qui change en janvier »).
- Les médias (Le Monde, franceinfo, L'Étudiant, Ouest-France…) servent à **repérer** une actu ; chaque chiffre/date
  affiché doit être **confirmé sur une source officielle**. Une simple annonce non publiée au BO → tampon « ANNONCE »
  et le dire clairement (« le ministre a annoncé… »). Rumeur, polémique politique ou info non confirmée → on n'en parle pas.
- **Vraie info ou fake news ? (règle prioritaire, demandée par l'utilisateur)** — une info n'est publiée que si
  TOUTES ces conditions sont remplies, sinon on change de sujet :
  1. **Source primaire officielle** trouvée et lue : la page elle-même sur un domaine officiel exact
     (education.gouv.fr, eduscol.education.gouv.fr, service-public.fr, legifrance.gouv.fr, parcoursup.fr, onisep.fr,
     etudiant.gouv.fr, site d'une académie en ac-*.fr). Méfie-toi des domaines qui imitent (« education-gouv.fr »,
     « .com » …) et des captures d'écran.
  2. **Date vérifiée** : la page est datée et l'info concerne la session / l'année en cours (pas une vieille actu
     qui recircule, pas une ancienne réforme abandonnée).
  3. Si l'info vient d'un média : **au moins deux médias reconnus et indépendants** la rapportent ET la source
     officielle la confirme. Une info vue seulement sur TikTok, X, Instagram, un forum, un site satirique (Le Gorafi…)
     ou un seul média = **rejetée**.
  4. Les chiffres et dates affichés sont **recopiés exactement** de la source officielle, sans arrondi ni extrapolation.
  5. Projet, consultation ou déclaration d'un ministre pas encore publiée au BO / Journal officiel → seulement avec le
     tampon « ANNONCE » et le mot « annoncé », jamais présenté comme acté.
  6. En cas de doute, contradiction entre sources ou sujet polémique → on ne publie pas cette info.
  Note dans `historique.json` (champ `sources`) **les URL exactes** utilisées, et cite la source officielle dans la
  vidéo et la légende.
- `stamp` : « NEWS », « DATES », « À VENIR », « OFFICIEL » ou « ANNONCE ». Accroche avec l'échéance ou la nouveauté en 1re
  ligne (« Vacances de Noël : », « Parcoursup 2027 : », « Nouveau au brevet : »).
- Ne jamais refaire un sujet déjà traité les 14 derniers jours (historique.json, champ `sujet`), sauf mise à jour réelle.
- Légende : « (garde-la) » + l'appel à commenter + hashtags avec l'année de naissance du public concerné + #actu #education.
- Si aucune actu ni date ne passe ces règles, fais une Info brevet / bac classique sur un autre sujet que celle du matin.

**Design commun (22/11/2026, demande de l'utilisateur : « on se base sur ce modèle maintenant »)** : toutes les vidéos
(quiz, défi, info actu) et le carrousel ont le look de la vidéo « Brevet 2027 » : fond cahier à carreaux, logo et
bandeau bleu nuit, 1re ligne de l'accroche en or, cartes blanches bordées de bleu nuit. Le générateur le fait seul. La
fin des vidéos (score, XP, « Rejoins la Ligue », « Lien en bio ») ne change pas.

**Couverture / miniature (22/11/2026, style choisi par l'utilisateur)** : photo plein écran **en rapport avec le
sujet**, assombrie, logo + badge en haut, encadré bleu nuit avec le type (QUIZ DU JOUR / INFO BREVET / BAC / DÉFI DE
LA LIGUE) et **seulement le sujet de la vidéo**, tampon rouge. Pas de « 8 questions • +400 XP ». Dans chaque spec vidéo :
- `cover_text` : 2 lignes courtes qui disent de quoi parle la vidéo (ex. « Capitales, cœur,
Charlemagne, la Loire… »,
  « Brevet 2027 :
le calcul de ta note », « Vacances de Noël :
les dates par zone ») ;
- `cover_image_query` : 2-3 mots en anglais pour la photo (sinon la photo de la 1re question est reprise ; obligatoire
  pour une info). Pas de personne reconnaissable, ni marque, ni logo : vérifie la 1re image de la vidéo et change la
  requête si la photo est hors sujet.

**Voix off (22/11/2026)** : le générateur adapte le texte avant de le faire lire (« 8/8 » → « 8 sur 8 », « 3e » →
« troisième », « 1re » → « première », « Tle » → « terminale », dates « 14/06/2027 » → « 14 juin 2027 », « 8h30 » →
« 8 heures 30 », « % », « n° », sigles BO/DNB/AB/TB, mots EN CAPITALES lus normalement, retour à la ligne = pause si
une nouvelle phrase commence). Écris quand même des phrases bien ponctuées et accentuées (é, è, à, ç…) dans les `dit`,
et mets un `dit` dès qu'un mot risque d'être mal lu (sigle rare, nom étranger, formule).

**Carrousel « Le savais-tu ? » (`type: "carrousel"`, 22/11/2026)** — un post photo pour changer des vidéos :
- Spec : `{"type":"carrousel","badge":"LE SAVAIS-TU ?","hook":"3 règles que tout le monde\noublie au contrôle",
  "infos":[{"badge":"6e • FRANÇAIS","title":"a ou à ?","lines":["Remplace par « avait » :","si ça marche, c'est « a »"],
  "example":"Il a (avait) faim / Il va à Paris"}, … exactement 3 infos …]}`. `lines` : 2 ou 3 lignes ≤ 32 caractères.
- Commande : `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-savais.jpg` → écrit `…-savais-1.jpg` à `-5.jpg`
  (1080×1350). Regarde les 5 images avant de publier.
- Publication Posty : un `create_media_upload` + PUT + `complete_media_upload` par image (contentType image/jpeg,
  width 1080, height 1350), puis `create_post` avec les 5 `mediaIds` **dans l'ordre**. Réseaux : Instagram (carrousel) ;
  TikTok en mode photo si Posty l'accepte (metadata `{"privacyLevel": "PUBLIC_TO_EVERYONE", "allowComment": true, "allowDuet": true, "allowStitch": true}`) — si le submit refuse TikTok,
  retire le contenu TikTok (`delete_post_content`) et publie sur Instagram seul, en le signalant. **Pas de YouTube.**
- Légende : accroche + « (garde-le 📌) » + « Glisse pour voir les 3 infos 👉 » + appel à commenter + « Révise comme
  dans un jeu sur RéviLeague 🏆 (lien en bio) » + hashtags.

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
3. `python3 generateur/make_reel.py spec.json reels/AAAA-MM-JJ-<quiz|info|actu|defi>.mp4`, puis extraire des images
   avec ffmpeg (la 1re image = couverture automatique, puis une par question / info) et les regarder.
   Le script affiche « Voix off : oui/non » : si c'est « non » ou si Fish Audio échoue, le signaler dans le message final.
4. Choisir l'heure de publication (règle « Heure de publication variable » ci-dessus).
5. Commit + push sur `main` (vidéo + ajout à `historique.json`, une entrée par question / info, avec `heure_publication`
   et `publie_a`).
6. **Programmer** via Posty : `create_media_upload` → PUT du fichier sur `uploadUrl` avec tous les `uploadHeaders` →
   `complete_media_upload` → `create_post` (3 contenus, **`scheduledAt` = l'heure choisie**, ISO avec le décalage
   de Paris, ex. `2026-11-21T09:37:00+01:00`) → `act_on_post` submit (skipApproval) → `act_on_post` publish **at: scheduled**
   → `get_post` doit montrer le post programmé à la bonne heure. TikTok : metadata `{"privacyLevel": "PUBLIC_TO_EVERYONE", "allowComment": true, "allowDuet": true, "allowStitch": true}`.
   **Ne jamais oublier `allowComment: true`** : sans lui, Posty envoie `false` par défaut et la vidéo sort avec les
   commentaires désactivés (constaté le 22/11/2026 sur toutes les vidéos TikTok publiées jusque-là).
   YouTube : metadata `{"title": ≤ 100 caractères, "privacyStatus": "public", "visibility": "public"}`, description
   avec le lien du site et #shorts. (Le 20/11/2026, toutes les vidéos YouTube étaient arrivées en **privé** : sans ces
   deux champs, Posty les envoie peut-être en privé. Au contrôle de l'étape 8, ouvre le lien YouTube : si la page dit
   « Vidéo privée », signale-le dans la notification.)
7. Légende Instagram / TikTok : 1 phrase d'accroche + appel à commenter (« Ton score ? ») + « Révise comme dans un jeu
   sur RéviLeague 🏆 (lien en bio) » + 5 à 8 hashtags pertinents (#revisions #brevet #bac #college #lycee + matières).
8. **Contrôle de la publication précédente** : chaque routine relit avec `get_post` le post programmé par la routine
   d'avant (dernier `posty_post_id` de `historique.json`) et note dans l'historique le statut par réseau. Si Instagram a
   échoué : publier en secours avec Windsor `execute_action` (`create_video_post`, params
   `{video_url, caption, share_to_feed: true}`) à partir de l'URL GitHub Pages (vérifiée avec WebFetch). Commit + push.

En cas d'échec (publication refusée, accès GitHub/Posty perdu) : ne pas réessayer en boucle, notifier l'utilisateur avec la cause.
