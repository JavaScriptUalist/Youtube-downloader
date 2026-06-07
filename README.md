# Video Downloader

Téléchargeur vidéo en ligne de commande, écrit en Python.  
Il utilise [yt-dlp](https://github.com/yt-dlp/yt-dlp). **Avec ffmpeg**, il télécharge la meilleure vidéo + le meilleur audio et les fusionne (1080p, 4K…). **Sans ffmpeg**, il se limite aux formats déjà fusionnés (souvent 360p–720p).

Licence : [MIT](LICENSE) — libre d'utilisation, modification et redistribution.

## Plateformes supportées

| Plateforme | Exemples de liens |
|------------|-------------------|
| **YouTube** | `watch?v=…`, `youtu.be/…`, Shorts, live |
| **Facebook** | `/watch`, `/reel`, `/video`, `fb.watch/…` |
| **Instagram** | `/p/…`, `/reel/…`, `/reels/…`, `/tv/…` |
| **TikTok** | `tiktok.com/@user/video/…`, `vm.tiktok.com/…` |

## Fonctionnalités

- Interface terminal simple (coller un lien, télécharger)
- **YouTube, Facebook, Instagram et TikTok** via leur URL
- Sélection automatique du meilleur format pré-fusionné disponible
- Barre de progression, vitesse et ETA
- Compatible **yt-dlp 2026+** (runtime JavaScript Node/Deno + scripts EJS pour YouTube)
- Ignore les paramètres de playlist YouTube (`list=`, radio, mix)
- Enregistrement dans le dossier `Téléchargements` de l'utilisateur

## Prérequis

| Composant | Obligatoire | Notes |
|-----------|-------------|-------|
| Python 3.10+ | Oui | |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) + EJS | Oui | via `yt-dlp[default]` |
| Node.js 22+ **ou** Deno 2.3+ | Recommandé | requis pour YouTube ([doc EJS](https://github.com/yt-dlp/yt-dlp/wiki/EJS)) |
| **ffmpeg** | Recommandé | **meilleure qualité** (fusion vidéo + audio) ; sans lui, résolution limitée |

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

### ffmpeg (recommandé pour la meilleure qualité)

Le script détecte ffmpeg automatiquement. S'il est installé, il télécharge la **meilleure vidéo** et la **meilleure piste audio**, puis les fusionne en MP4.

```bash
winget install Gyan.FFmpeg
```

Fermez et rouvrez le terminal après l'installation. Au lancement, vous devez voir :

```
ffmpeg : détecté (meilleure qualité disponible)
Mode     : haute qualité (ffmpeg)
```

## Utilisation

```bash
python downloadyt.py
```

1. Collez l'URL d'une vidéo (YouTube, Facebook, Instagram ou TikTok)
2. Le script détecte la plateforme, analyse les formats et lance le téléchargement
3. Tapez `q` pour quitter

Les fichiers sont enregistrés dans :

- **Windows** : `C:\Users\<vous>\Téléchargements`
- **Linux / macOS** : `~/Téléchargements`

## Exemple

```
╔══════════════════════════════════════════╗
║   Video Downloader                       ║
╚══════════════════════════════════════════╝

  Plateformes : YouTube, Facebook, Instagram, TikTok

  Runtime JS : node (YouTube)
  ffmpeg : détecté (meilleure qualité disponible)

  Colle le lien vidéo (ou 'q' pour quitter) : https://www.youtube.com/watch?v=...
```

## Limitations

- **Sans ffmpeg** : seuls les formats déjà fusionnés sont disponibles (souvent 360p–720p)
- **Avec ffmpeg** : meilleure qualité possible selon la vidéo source (1080p, 4K…)
- Certaines vidéos peuvent être privées, géo-bloquées ou supprimées
- **Instagram / Facebook** : contenus privés ou stories peuvent exiger une connexion (non géré par défaut)
- **TikTok** : certains liens régionaux ou expirés peuvent échouer
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

Respectez les conditions d'utilisation de chaque plateforme (YouTube, Meta, TikTok) et les droits d'auteur.  
Cet outil est fourni à des fins éducatives ; l'auteur n'est pas responsable de son usage.

## Remerciements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — moteur de téléchargement
