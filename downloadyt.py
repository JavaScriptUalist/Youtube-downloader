#!/usr/bin/env python3
"""
Téléchargeur vidéo multi-plateformes
YouTube, Facebook, Instagram, TikTok via yt-dlp.
Avec ffmpeg : meilleure qualité (vidéo + audio fusionnés).
Sans ffmpeg : formats pré-fusionnés uniquement.
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

# (id interne, nom affiché, motifs d'URL)
SUPPORTED_PLATFORMS: list[tuple[str, str, list[str]]] = [
    (
        "youtube",
        "YouTube",
        [
            r"(?:https?://)?(?:www\.|m\.)?youtube\.com/(?:watch\?[^\s#]*v=|shorts/|live/)",
            r"(?:https?://)?youtu\.be/[\w-]+",
        ],
    ),
    (
        "facebook",
        "Facebook",
        [
            r"(?:https?://)?(?:www\.|m\.|web\.)?(?:facebook\.com|fb\.com)/"
            r"(?:watch|reel|reels|video|videos|share/r|share/v|[^/?\s]+/videos)/",
            r"(?:https?://)?(?:www\.)?fb\.watch/[\w-]+",
        ],
    ),
    (
        "instagram",
        "Instagram",
        [
            r"(?:https?://)?(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[\w-]+",
        ],
    ),
    (
        "tiktok",
        "TikTok",
        [
            r"(?:https?://)?(?:www\.|vm\.|vt\.)?tiktok\.com/"
            r"(?:@[\w.-]+/video/[\d]+|t/[\w-]+|[\w-]+)",
        ],
    ),
]

_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "igsh", "igshid", "si", "feature", "is_from_webapp",
})


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


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _find_js_runtime() -> dict:
    """Active Node (prioritaire) ou Deno pour l'extraction YouTube (yt-dlp EJS)."""
    if shutil.which("node"):
        return {"node": {}}
    if shutil.which("deno"):
        return {"deno": {}}
    return {}


def detect_platform(url: str) -> tuple[str, str] | None:
    """Retourne (id_plateforme, nom_affiché) ou None si URL non reconnue."""
    cleaned = url.strip()
    for platform_id, display_name, patterns in SUPPORTED_PLATFORMS:
        if any(re.search(p, cleaned, re.IGNORECASE) for p in patterns):
            return platform_id, display_name
    return None


def normalize_url(url: str, platform: str) -> str:
    """Nettoie l'URL selon la plateforme."""
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")

    if platform == "youtube":
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/").split("/")[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
            return url.strip()

        qs = parse_qs(parsed.query)
        video_id = (qs.get("v") or [None])[0]
        if video_id:
            return urlunparse(parsed._replace(
                query=urlencode({"v": video_id}),
                fragment="",
            ))
        return urlunparse(parsed._replace(fragment=""))

    qs = parse_qs(parsed.query, keep_blank_values=False)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in _TRACKING_PARAMS}
    return urlunparse(parsed._replace(
        query=urlencode(clean_qs, doseq=True),
        fragment="",
    ))


def base_ydl_opts(platform: str, **extra) -> dict:
    opts: dict = {"noplaylist": True}
    if platform == "youtube":
        opts["js_runtimes"] = _find_js_runtime()
        opts["extractor_args"] = {"youtube": {"player_client": ["android", "web"]}}
    opts.update(extra)
    return opts


def is_supported_url(url: str) -> bool:
    return detect_platform(url) is not None


def _format_size_str(fmt: dict) -> str:
    sz = fmt.get("filesize") or fmt.get("filesize_approx")
    return f"{sz / 1_048_576:.1f} Mo" if sz else "taille inconnue"


def _extract_formats(url: str, platform: str) -> list[dict]:
    import yt_dlp

    url = normalize_url(url, platform)
    with yt_dlp.YoutubeDL(base_ydl_opts(platform, quiet=True, no_warnings=True)) as ydl:
        info = ydl.extract_info(url, download=False)
    return info.get("formats", [])


def select_download_profile(url: str, platform: str) -> tuple[str, list, list, str]:
    """
    Retourne (format_id, aperçu, postprocessors, mode).
    Avec ffmpeg : meilleure vidéo + meilleur audio fusionnés.
    Sans ffmpeg : meilleur format déjà fusionné.
    """
    formats = _extract_formats(url, platform)

    if has_ffmpeg():
        video_only = [
            f for f in formats
            if f.get("vcodec") not in (None, "none")
            and f.get("acodec") in (None, "none")
        ]
        video_only.sort(
            key=lambda f: (
                f.get("height") or 0,
                f.get("filesize") or f.get("filesize_approx") or 0,
            ),
            reverse=True,
        )

        preview = []
        for f in video_only[:5]:
            h   = f.get("height", "?")
            ext = f.get("ext", "?")
            fps = f.get("fps", "?")
            preview.append(
                f"  {f['format_id']:>10}  {h}p  {fps}fps  {ext}  {_format_size_str(f)}"
            )

        fmt = "bestvideo*+bestaudio/best"
        postprocessors = [{"key": "FFmpegMerger"}]
        return fmt, preview, postprocessors, "haute qualité (ffmpeg)"

    combined = [
        f for f in formats
        if f.get("vcodec") not in (None, "none")
        and f.get("acodec") not in (None, "none")
    ]

    if not combined:
        return "best[ext=mp4]/best[ext=webm]/best", [], [], "standard (sans ffmpeg)"

    combined.sort(
        key=lambda f: (
            f.get("height") or 0,
            f.get("filesize") or f.get("filesize_approx") or 0,
        ),
        reverse=True,
    )

    preview = []
    for f in combined[:5]:
        h   = f.get("height", "?")
        ext = f.get("ext", "?")
        fps = f.get("fps", "?")
        preview.append(
            f"  {f['format_id']:>10}  {h}p  {fps}fps  {ext}  {_format_size_str(f)}"
        )

    return combined[0]["format_id"], preview, [], "pré-fusionné (sans ffmpeg)"


def download_video(url: str, output_dir: str = ".") -> None:
    import yt_dlp

    detected = detect_platform(url)
    if not detected:
        raise ValueError("URL non reconnue.")

    platform, platform_name = detected
    url = normalize_url(url, platform)

    print(f"\n{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}  Plateforme :{RESET} {platform_name}")
    print(f"{BOLD}  Analyse des formats disponibles…{RESET}")

    fmt_id, preview, postprocessors, mode = select_download_profile(url, platform)
    print(f"  {BOLD}Mode     :{RESET} {mode}")

    if preview:
        label = (
            "Pistes vidéo disponibles (top 5, audio fusionné par ffmpeg)"
            if has_ffmpeg()
            else "Formats pré-fusionnés détectés (top 5)"
        )
        print(f"\n  {YELLOW}{label} :{RESET}")
        for line in preview:
            print(line)

    print(f"\n  {GREEN}→ Sélectionné : {fmt_id}{RESET}")

    ydl_opts = base_ydl_opts(
        platform,
        format=fmt_id,
        outtmpl=os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        progress_hooks=[progress_hook],
        postprocessors=postprocessors,
        quiet=False,
        no_warnings=False,
    )
    if postprocessors:
        ydl_opts["merge_output_format"] = "mp4"

    print(f"\n{BOLD}  Démarrage du téléchargement…{RESET}")
    print(f"{CYAN}{'─'*55}{RESET}\n")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title    = info.get("title", "Inconnue")
        duration = info.get("duration") or 0
        uploader = info.get("uploader") or info.get("channel") or "Inconnu"
        mins, secs = divmod(int(duration), 60)

        print(f"  {BOLD}Titre    :{RESET} {title}")
        print(f"  {BOLD}Auteur   :{RESET} {uploader}")
        if duration:
            print(f"  {BOLD}Durée    :{RESET} {mins:02d}:{secs:02d}")
        print()

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


def _supported_platforms_hint() -> str:
    return ", ".join(name for _, name, _ in SUPPORTED_PLATFORMS)


def main() -> None:
    check_dependencies()

    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║   Video Downloader                       ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════╝{RESET}\n")
    print(f"  {BOLD}Plateformes :{RESET} {_supported_platforms_hint()}\n")

    runtime = _find_js_runtime()
    if runtime:
        name = next(iter(runtime))
        print(f"  {GREEN}Runtime JS :{RESET} {name} {YELLOW}(YouTube){RESET}")
    else:
        print(f"  {YELLOW}Runtime JS :{RESET} aucun {YELLOW}(YouTube uniquement){RESET}")
        print(f"  → https://github.com/yt-dlp/yt-dlp/wiki/EJS\n")

    if has_ffmpeg():
        print(f"  {GREEN}ffmpeg :{RESET} détecté (meilleure qualité disponible)\n")
    else:
        print(f"  {YELLOW}ffmpeg :{RESET} absent (formats pré-fusionnés uniquement)")
        print(f"  → Installe : {CYAN}winget install Gyan.FFmpeg{RESET}\n")

    output_dir = os.path.join(os.path.expanduser("~"), "Téléchargements")
    os.makedirs(output_dir, exist_ok=True)

    while True:
        try:
            url = input(
                f"{BOLD}  Colle le lien vidéo{RESET} (ou 'q' pour quitter) : "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n  {YELLOW}Annulé.{RESET}")
            break

        if url.lower() in ("q", "quit", "exit"):
            print(f"\n  {YELLOW}Au revoir !{RESET}\n")
            break

        if not url:
            print(f"  {RED}Lien vide, réessaie.{RESET}\n")
            continue

        if not is_supported_url(url):
            print(f"  {RED}URL non reconnue.{RESET}")
            print(f"  Plateformes acceptées : {_supported_platforms_hint()}\n")
            continue

        try:
            download_video(url, output_dir=output_dir)
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
