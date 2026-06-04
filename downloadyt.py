#!/usr/bin/env python3
"""
Téléchargeur YouTube – sans ffmpeg
Utilise les formats pré-fusionnés (vidéo + audio dans un seul fichier).
Dépendance : yt-dlp  →  pip install yt-dlp
"""

import sys
import os
import re
import shutil
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# ── Couleurs terminal ──────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def check_dependencies():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        print(f"{RED}[ERREUR]{RESET} yt-dlp n'est pas installé.")
        print(f"  → Lance : {CYAN}pip install -U \"yt-dlp[default]\"{RESET}")
        sys.exit(1)

    try:
        import yt_dlp_ejs  # noqa: F401
    except ImportError:
        print(f"{YELLOW}[AVERTISSEMENT]{RESET} yt-dlp-ejs manquant (scripts YouTube).")
        print(f"  → Lance : {CYAN}pip install -U \"yt-dlp[default]\"{RESET}\n")


def _find_js_runtime() -> dict:
    """Active Node (prioritaire) ou Deno pour l'extraction YouTube (yt-dlp EJS)."""
    if shutil.which("node"):
        return {"node": {}}
    if shutil.which("deno"):
        return {"deno": {}}
    return {}


def normalize_youtube_url(url: str) -> str:
    """Ne garde que la vidéo ciblée (ignore list=, radio, mix, etc.)."""
    parsed = urlparse(url.strip())
    if "youtube.com" not in parsed.netloc and "youtu.be" not in parsed.netloc:
        return url.strip()

    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.lstrip("/").split("/")[0]
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return url.strip()

    qs = parse_qs(parsed.query)
    video_id = (qs.get("v") or [None])[0]
    if not video_id:
        return url.strip()

    clean_qs = urlencode({"v": video_id})
    return urlunparse(parsed._replace(query=clean_qs, fragment=""))


def base_ydl_opts(**extra) -> dict:
    opts = {
        "noplaylist": True,
        "js_runtimes": _find_js_runtime(),
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    opts.update(extra)
    return opts


def is_valid_youtube_url(url: str) -> bool:
    patterns = [
        r"(https?://)?(www\.)?(youtube\.com/watch\?v=[\w-]+)",
        r"(https?://)?(youtu\.be/[\w-]+)",
        r"(https?://)?(www\.)?(youtube\.com/shorts/[\w-]+)",
        r"(https?://)?(www\.)?(youtube\.com/live/[\w-]+)",
    ]
    return any(re.match(p, url.strip()) for p in patterns)


def get_best_no_merge_format(url: str) -> tuple[str, list]:
    """
    Analyse les formats disponibles et retourne le meilleur format
    pré-fusionné (vidéo+audio dans le même fichier), sans ffmpeg.
    Retourne (format_id, liste_formats_affichée).
    """
    import yt_dlp

    url = normalize_youtube_url(url)
    with yt_dlp.YoutubeDL(base_ydl_opts(quiet=True, no_warnings=True)) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = info.get("formats", [])

    # Garde uniquement les formats qui ont DÉJÀ vidéo + audio
    combined = [
        f for f in formats
        if f.get("vcodec") not in (None, "none")
        and f.get("acodec") not in (None, "none")
    ]

    if not combined:
        return "best", []

    # Trie par hauteur (résolution) décroissante, puis par filesize
    combined.sort(
        key=lambda f: (
            f.get("height") or 0,
            f.get("filesize") or f.get("filesize_approx") or 0,
        ),
        reverse=True,
    )

    best = combined[0]

    # Résumé des 5 premiers pour info
    preview = []
    for f in combined[:5]:
        h   = f.get("height", "?")
        ext = f.get("ext", "?")
        fps = f.get("fps", "?")
        sz  = f.get("filesize") or f.get("filesize_approx")
        sz_str = f"{sz / 1_048_576:.1f} Mo" if sz else "taille inconnue"
        preview.append(f"  {f['format_id']:>10}  {h}p  {fps}fps  {ext}  {sz_str}")

    return best["format_id"], preview


def download_video(url: str, output_dir: str = ".") -> None:
    import yt_dlp

    print(f"\n{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}  Analyse des formats disponibles…{RESET}")

    fmt_id, preview = get_best_no_merge_format(url)

    if preview:
        print(f"\n  {YELLOW}Formats pré-fusionnés détectés (top 5) :{RESET}")
        for line in preview:
            print(line)
        print(f"\n  {GREEN}→ Sélectionné : format {fmt_id}{RESET}")

    url = normalize_youtube_url(url)
    ydl_opts = base_ydl_opts(
        format=fmt_id,
        outtmpl=os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        progress_hooks=[progress_hook],
        postprocessors=[],
        quiet=False,
        no_warnings=False,
    )

    print(f"\n{BOLD}  Démarrage du téléchargement…{RESET}")
    print(f"{CYAN}{'─'*55}{RESET}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title    = info.get("title", "Inconnue")
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "Inconnu")
        mins, secs = divmod(duration, 60)

        print(f"  {BOLD}Titre    :{RESET} {title}")
        print(f"  {BOLD}Chaîne   :{RESET} {uploader}")
        print(f"  {BOLD}Durée    :{RESET} {mins:02d}:{secs:02d}\n")

        ydl.download([url])


_last_filename = ""

def progress_hook(d: dict) -> None:
    global _last_filename

    if d["status"] == "downloading":
        filename   = os.path.basename(d.get("filename", ""))
        downloaded = d.get("_downloaded_bytes_str", "?")
        total      = d.get("_total_bytes_str") or d.get("_total_bytes_estimate_str", "?")
        speed      = d.get("_speed_str", "?")
        eta        = d.get("_eta_str", "?")
        percent    = d.get("_percent_str", "  ?%").strip()

        if filename != _last_filename:
            _last_filename = filename
            print(f"\n  {YELLOW}Fichier :{RESET} {filename}")

        bar_len = 30
        try:
            pct = float(percent.replace("%", ""))
            filled = int(bar_len * pct / 100)
        except ValueError:
            filled = 0

        bar = f"{GREEN}{'█' * filled}{RESET}{'░' * (bar_len - filled)}"
        print(
            f"\r  [{bar}] {BOLD}{percent:>6}{RESET}"
            f"  {downloaded}/{total}"
            f"  ↓ {speed}"
            f"  ETA {eta}   ",
            end="",
            flush=True,
        )

    elif d["status"] == "finished":
        print(f"\n\n  {GREEN}✔  Téléchargement terminé !{RESET}")

    elif d["status"] == "error":
        print(f"\n  {RED}✘  Erreur durant le téléchargement.{RESET}")


def main() -> None:
    check_dependencies()

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║   YouTube Downloader – Sans ffmpeg       ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════╝{RESET}\n")

    runtime = _find_js_runtime()
    if runtime:
        name = next(iter(runtime))
        print(f"  {GREEN}Runtime JS :{RESET} {name}")
    else:
        print(f"  {YELLOW}Runtime JS :{RESET} aucun (installe Node ou Deno)")
        print(f"  → https://github.com/yt-dlp/yt-dlp/wiki/EJS\n")

    if not shutil.which("ffmpeg"):
        print(f"  {YELLOW}ffmpeg :{RESET} absent (formats pré-fusionnés uniquement)\n")

    output_dir = os.path.join(os.path.expanduser("~"), "Téléchargements")
    os.makedirs(output_dir, exist_ok=True)

    while True:
        try:
            url = input(f"{BOLD}  Colle le lien YouTube{RESET} (ou 'q' pour quitter) : ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {YELLOW}Annulé.{RESET}")
            break

        if url.lower() in ("q", "quit", "exit"):
            print(f"\n  {YELLOW}Au revoir !{RESET}\n")
            break

        if not url:
            print(f"  {RED}Lien vide, réessaie.{RESET}\n")
            continue

        if not is_valid_youtube_url(url):
            print(f"  {RED}URL non reconnue comme lien YouTube valide.{RESET}\n")
            continue

        try:
            download_video(normalize_youtube_url(url), output_dir=output_dir)
            print(f"\n  {CYAN}Enregistré dans : {output_dir}{RESET}\n")
        except Exception as exc:
            print(f"\n  {RED}Échec : {exc}{RESET}\n")

        again = input(f"  {BOLD}Télécharger une autre vidéo ?{RESET} [o/N] : ").strip().lower()
        if again not in ("o", "oui", "y", "yes"):
            print(f"\n  {YELLOW}Au revoir !{RESET}\n")
            break
        print()


if __name__ == "__main__":
    main()
