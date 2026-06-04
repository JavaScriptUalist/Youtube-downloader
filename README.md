# YouTube Downloader (sans ffmpeg)

Téléchargeur YouTube en ligne de commande, écrit en Python.  
Il utilise [yt-dlp](https://github.com/yt-dlp/yt-dlp) et cible les **formats pré-fusionnés** (vidéo + audio dans un seul fichier), donc **ffmpeg n'est pas obligatoire**.

Licence : [MIT](LICENSE) — libre d'utilisation, modification et redistribution.

## Fonctionnalités

- Interface terminal simple (coller un lien, télécharger)
- Sélection automatique du meilleur format pré-fusionné disponible
- Barre de progression, vitesse et ETA
- Compatible **yt-dlp 2026+** (runtime JavaScript Node/Deno + scripts EJS)
- Ignore les paramètres de playlist (`list=`, radio, mix) — une seule vidéo à la fois
- Enregistrement dans le dossier `Téléchargements` de l'utilisateur

## Prérequis

| Composant | Obligatoire | Notes |
|-----------|-------------|-------|
| Python 3.10+ | Oui | |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) + EJS | Oui | via `yt-dlp[default]` |
| Node.js 22+ **ou** Deno 2.3+ | Recommandé | requis pour l'extraction YouTube ([doc EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS)) |
| ffmpeg | Non | améliore la qualité et le choix des formats |

## Installation

```bash
git clone https://github.com/JavaScriptUalist/Youtube-downloader.git
cd Youtube-downloader
pip install -r requirements.txt
```

Ou sans cloner :

```bash
pip install -U "yt-dlp[default]"
```

Puis téléchargez `downloadyt.py` depuis ce dépôt.

### Node.js (recommandé si absent)

- Windows : [nodejs.org](https://nodejs.org/) ou `winget install OpenJS.NodeJS.LTS`
- Deno (alternative) : [docs.deno.com](https://docs.deno.com/runtime/getting_started/installation/)

### ffmpeg (optionnel)

```bash
winget install Gyan.FFmpeg
```

## Utilisation

```bash
python downloadyt.py
```

1. Collez l'URL YouTube (`watch`, `youtu.be`, Shorts, live)
2. Le script analyse les formats et lance le téléchargement
3. Tapez `q` pour quitter

Les fichiers sont enregistrés dans :

- **Windows** : `C:\Users\<vous>\Téléchargements`
- **Linux / macOS** : `~/Téléchargements`

## Exemple

```
╔══════════════════════════════════════════╗
║   YouTube Downloader – Sans ffmpeg       ║
╚══════════════════════════════════════════╝

  Runtime JS : node
  ffmpeg : absent (formats pré-fusionnés uniquement)

  Colle le lien YouTube (ou 'q' pour quitter) : https://www.youtube.com/watch?v=...
```

## Limitations

- Sans ffmpeg, seuls les formats déjà fusionnés (souvent 360p–720p) sont disponibles
- Certaines vidéos peuvent être privées, géo-bloquées ou supprimées
- YouTube change régulièrement son API : mettez **yt-dlp** à jour en cas de problème

```bash
pip install -U "yt-dlp[default]"
```

## Dépannage

| Message | Action |
|---------|--------|
| `yt-dlp n'est pas installé` | `pip install -U "yt-dlp[default]"` |
| `Runtime JS : aucun` | Installez Node ou Deno |
| Avalanche de warnings avec `&list=` | Mettez à jour le script (normalisation d'URL incluse) |
| `Some android client https formats have been skipped` | Avertissement YouTube/SABR, souvent non bloquant |
| `This video is not available` | Vidéo indisponible ou restriction régionale |

## Contribuer

Les issues et pull requests sont les bienvenues.

1. Forkez le projet
2. Créez une branche (`git checkout -b feature/ma-fonctionnalite`)
3. Committez et poussez
4. Ouvrez une Pull Request

## Avertissement légal

Respectez les [Conditions d'utilisation de YouTube](https://www.youtube.com/t/terms) et les droits d'auteur.  
Ce outil est fourni à des fins éducatives ; l'auteur n'est pas responsable de son usage.

## Remerciements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — moteur de téléchargement
