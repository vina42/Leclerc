# Veille promotions E.Leclerc — prototype cloud

Ce projet est conçu pour s'exécuter quotidiennement sur GitHub Actions, même lorsque votre ordinateur est éteint.

## Fonctionnement
- Consulte la page publique https://www.e.leclerc/prospectus
- Recherche les liens PDF accessibles directement
- Extrait le texte des PDF trouvés
- Repère les mentions susceptibles de signaler une réduction immédiate, un avantage fidélité ou un produit offert
- Produit un fichier Excel téléchargeable dans les artefacts de l'exécution GitHub Actions

## Limites
Le site peut présenter les catalogues dans une visionneuse ou sous forme d'images, et pas comme des PDF directs. Dans ce cas, cette version le signalera : il faudra adapter la collecte au format réellement utilisé. Le prototype ne contourne pas de connexion, CAPTCHA ou protection technique.
Les lignes extraites sont des offres candidates à vérifier, pas une garantie d'exhaustivité. Le prix, les dates, le magasin et les conditions doivent être vérifiés.

## Installation
1. Créez un dépôt GitHub privé.
2. Décompressez ce projet et téléversez tous les fichiers dans le dépôt.
3. Dans GitHub, ouvrez l'onglet **Actions** et autorisez les workflows si demandé.
4. Lancez **Veille promotions E.Leclerc** via **Run workflow** pour le premier test.
5. Téléchargez l'artefact `rapport-promotions-leclerc` à la fin de l'exécution.

Le workflow est planifié chaque jour à 06:17 UTC. Les tâches planifiées peuvent parfois être retardées par GitHub.

Pour une vraie collecte exhaustive, il faudra valider la façon dont les catalogues sont publiés pour le magasin ou le périmètre retenu, puis ajouter si nécessaire l'accès aux pages de visionneuse et l'OCR.
