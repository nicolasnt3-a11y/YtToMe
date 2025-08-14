import os
import re
import sys
import threading
import unicodedata
from pathlib import Path
import shutil
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from yt_dlp import YoutubeDL
except Exception:
    YoutubeDL = None

# Pour charger et dessiner le PNG / icône check
try:
    from PIL import Image, ImageTk, ImageDraw
except Exception:
    Image = None
    ImageTk = None
    ImageDraw = None


def sanitize_filename(raw_title: str) -> str:
    """Retourne un nom de fichier sans accents, sans caractères spéciaux, sans espaces.

    - Supprime les accents via NFKD
    - Transforme en minuscules
    - Remplace les séquences non autorisées par '-'
    - Supprime les espaces
    - Garde uniquement [a-z0-9-]
    """
    if not raw_title:
        return "video"

    normalized = unicodedata.normalize("NFKD", raw_title)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    no_spaces = re.sub(r"\s+", "", lowered)
    safe = re.sub(r"[^a-z0-9-]", "-", no_spaces)
    safe = re.sub(r"-+", "-", safe).strip("-")
    return safe or "video"


def get_default_download_dir() -> str:
    downloads = Path.home() / "Downloads"
    return str(downloads if downloads.exists() else Path.cwd())


def ensure_ffmpeg_available() -> Optional[str]:
    """Retourne le chemin vers FFmpeg, en essayant dans cet ordre:
    - Un exécutable à côté de app.py (ffmpeg.exe/ffmpeg)
    - Le PATH système
    - Téléchargement via imageio-ffmpeg (puis copie à côté de app.py)
    """
    script_dir = Path(__file__).resolve().parent

    for name in ("ffmpeg.exe", "ffmpeg"):
        p = script_dir / name
        if p.exists():
            return str(p)

    from_path = shutil.which("ffmpeg")
    if from_path:
        return from_path

    try:
        import imageio_ffmpeg as iio_ffmpeg
        bin_path = iio_ffmpeg.get_ffmpeg_exe()
        target = script_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if not target.exists():
            try:
                shutil.copyfile(bin_path, target)
                try:
                    os.chmod(target, 0o755)
                except Exception:
                    pass
                return str(target)
            except Exception:
                return bin_path
        return str(target)
    except Exception:
        return None


def find_png_icon_path() -> Optional[str]:
    """Renvoie le chemin du premier PNG trouvé à côté de app.py."""
    script_dir = Path(__file__).resolve().parent
    for png in script_dir.glob("*.png"):
        return str(png)
    return None


class QuietLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg, file=sys.stderr)


class YouTubeDownloaderGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("YT to me - Téléchargeur 720p")
        self.root.geometry("720x460")
        self.root.resizable(False, False)

        self.dir_var = tk.StringVar(value=get_default_download_dir())
        self.status_var = tk.StringVar(value="Prêt.")

        self.progress_value = tk.DoubleVar(value=0.0)
        self.last_downloaded_path = None
        self.current_title = None

        # Gestion de lot
        self.queue_urls: List[str] = []
        self.total_in_batch: int = 0
        self.completed_in_batch: int = 0
        self.current_url: Optional[str] = None
        self.batch_line_numbers: List[int] = []

        # Images
        self.icon_image = None
        self.display_image = None
        self.check_image = None

        self._build_ui()
        self._load_app_image()
        self._prepare_text_tags()

    def _build_ui(self):
        padx = 12
        pady = 8

        # URLs (multi-lignes)
        frm_url = ttk.Frame(self.root)
        frm_url.pack(fill="both", expand=True, padx=padx, pady=(pady, 4))
        lbl_url = ttk.Label(frm_url, text="URLs YouTube (une par ligne) :")
        lbl_url.pack(anchor="w")
        self.txt_urls = tk.Text(frm_url, height=8, wrap="word")
        self.txt_urls.pack(fill="both", expand=True)

        # Dossier
        frm_dir = ttk.Frame(self.root)
        frm_dir.pack(fill="x", padx=padx, pady=4)
        lbl_dir = ttk.Label(frm_dir, text="Dossier de téléchargement :")
        lbl_dir.pack(anchor="w")
        row_dir = ttk.Frame(frm_dir)
        row_dir.pack(fill="x")
        ent_dir = ttk.Entry(row_dir, textvariable=self.dir_var)
        ent_dir.pack(side="left", fill="x", expand=True)
        btn_browse = ttk.Button(row_dir, text="Parcourir...", command=self._choose_dir)
        btn_browse.pack(side="left", padx=(6, 0))

        # Actions
        frm_actions = ttk.Frame(self.root)
        frm_actions.pack(fill="x", padx=padx, pady=4)
        btn_dl = ttk.Button(frm_actions, text="Télécharger en 720p", command=self._start_batch_download)
        btn_dl.pack(side="left")

        # Progression
        frm_prog = ttk.Frame(self.root)
        frm_prog.pack(fill="x", padx=padx, pady=(6, 2))
        self.pbar = ttk.Progressbar(frm_prog, variable=self.progress_value, maximum=100)
        self.pbar.pack(fill="x")

        # Image sous la barre
        frm_logo = ttk.Frame(self.root)
        frm_logo.pack(fill="x", padx=padx, pady=(2, 2))
        self.image_label = ttk.Label(frm_logo)
        self.image_label.pack(anchor="center")

        # Statut
        frm_status = ttk.Frame(self.root)
        frm_status.pack(fill="x", padx=padx, pady=(2, pady))
        self.lbl_status = ttk.Label(frm_status, textvariable=self.status_var)
        self.lbl_status.pack(anchor="w")

    def _prepare_text_tags(self):
        # Tag pour marquer en vert
        try:
            self.txt_urls.tag_configure("done", foreground="#198754")
        except Exception:
            pass

    def _create_check_image(self):
        if Image is None or ImageDraw is None or ImageTk is None:
            return None
        # Icône check simple 14x14 avec fond transparent
        size = 14
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # Tracer un check vert
        # Segment 1
        draw.line([(3, 8), (6, 11)], fill="#198754", width=3)
        # Segment 2
        draw.line([(6, 11), (11, 3)], fill="#198754", width=3)
        return ImageTk.PhotoImage(img)

    def _load_app_image(self):
        path = find_png_icon_path()
        if path and Image is not None and ImageTk is not None:
            try:
                pil = Image.open(path)
                # Icône fenêtre
                icon_pil = pil.copy()
                icon_pil.thumbnail((64, 64))
                self.icon_image = ImageTk.PhotoImage(icon_pil)
                try:
                    self.root.iconphoto(True, self.icon_image)
                except Exception:
                    pass
                # Affichage sous la barre
                disp_pil = pil.copy()
                disp_pil.thumbnail((256, 256))
                self.display_image = ImageTk.PhotoImage(disp_pil)
                self.image_label.configure(image=self.display_image)
            except Exception:
                pass
        # Créer l'icône check
        self.check_image = self._create_check_image()

    def _choose_dir(self):
        d = filedialog.askdirectory(
            initialdir=self.dir_var.get() or get_default_download_dir(),
            title="Choisir un dossier",
        )
        if d:
            self.dir_var.set(d)

    def _set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def _set_progress(self, percent: float):
        self.progress_value.set(max(0.0, min(100.0, percent)))
        self.root.update_idletasks()

    def _toggle_controls(self, enabled: bool):
        state = "!disabled" if enabled else "disabled"
        for child in self.root.winfo_children():
            for sub in child.winfo_children():
                if isinstance(sub, ttk.Entry) or isinstance(sub, ttk.Button):
                    sub.state((state,))
                elif isinstance(sub, tk.Text):
                    sub.configure(state=("normal" if enabled else "disabled"))

    def _collect_urls(self) -> List[str]:
        raw = self.txt_urls.get("1.0", "end")
        urls = [u.strip() for u in raw.splitlines() if u.strip()]
        return urls

    def _compute_batch_line_numbers(self) -> List[int]:
        raw = self.txt_urls.get("1.0", "end")
        lines = raw.splitlines()
        line_numbers: List[int] = []
        for i, line in enumerate(lines, start=1):
            if line.strip():
                line_numbers.append(i)
        return line_numbers

    def _start_batch_download(self):
        out_dir = (self.dir_var.get() or "").strip()
        if not out_dir:
            messagebox.showwarning("Dossier manquant", "Veuillez choisir un dossier de téléchargement.")
            return
        urls = self._collect_urls()
        if not urls:
            messagebox.showwarning("URLs manquantes", "Collez une ou plusieurs URLs YouTube (une par ligne).")
            return
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        # Nettoyer anciens marquages
        try:
            self.txt_urls.tag_remove("done", "1.0", "end")
        except Exception:
            pass

        self.queue_urls = urls
        self.total_in_batch = len(urls)
        self.completed_in_batch = 0
        self.batch_line_numbers = self._compute_batch_line_numbers()
        self._toggle_controls(False)
        self._start_next_in_queue()

    def _start_next_in_queue(self):
        if not self.queue_urls:
            self._set_status("Tous les téléchargements sont terminés.")
            self._set_progress(0.0)
            self._toggle_controls(True)
            return
        self.current_url = self.queue_urls.pop(0)
        idx = self.completed_in_batch + 1
        self._set_status(f"[{idx}/{self.total_in_batch}] Préparation...")
        self._set_progress(0.0)
        out_dir = (self.dir_var.get() or "").strip()
        threading.Thread(target=self._download_worker, args=(self.current_url, out_dir), daemon=True).start()

    def _download_hook(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes") or 0
            percent = (done / total * 100.0) if total else 0.0
            self.root.after(0, self._set_progress, percent)
            speed = d.get("speed")
            spd = f" - {speed/1024:.1f} KiB/s" if speed else ""
            prefix = ""
            if self.total_in_batch:
                prefix = f"[{self.completed_in_batch + 1}/{self.total_in_batch}] "
            txt = f"{prefix}Téléchargement... {percent:.1f}%{spd}"
            self.root.after(0, self._set_status, txt)
        elif status == "finished":
            filename = d.get("filename")
            self.last_downloaded_path = filename
            self.root.after(0, self._set_status, "Téléchargement terminé, traitement...")
            self.root.after(0, self._set_progress, 100.0)
        elif status == "error":
            self.root.after(0, self._set_status, "Erreur durant le téléchargement.")

    def _mark_line_done(self, line_no: int):
        try:
            # Autoriser mise à jour temporaire
            was_disabled = str(self.txt_urls.cget("state")) == "disabled"
            if was_disabled:
                self.txt_urls.configure(state="normal")
            # Appliquer la couleur verte
            self.txt_urls.tag_add("done", f"{line_no}.0", f"{line_no}.end")
            # Ajouter l'icône check si disponible
            if self.check_image is not None:
                try:
                    self.txt_urls.image_create(f"{line_no}.end", image=self.check_image, padx=6)
                except Exception:
                    pass
            else:
                # Fallback: ajouter un caractère check en vert
                try:
                    self.txt_urls.insert(f"{line_no}.end", " ✔")
                    self.txt_urls.tag_add("done", f"{line_no}.end-2c", f"{line_no}.end")
                except Exception:
                    pass
            if was_disabled:
                self.txt_urls.configure(state="disabled")
        except Exception:
            pass

    def _after_item(self):
        # Marque la ligne correspondante comme terminée
        try:
            if 0 <= self.completed_in_batch < len(self.batch_line_numbers):
                line_no = self.batch_line_numbers[self.completed_in_batch]
                self._mark_line_done(line_no)
        except Exception:
            pass
        # Puis passe à l'élément suivant
        self.completed_in_batch += 1
        self.last_downloaded_path = None
        self.current_title = None
        self.current_url = None
        self._start_next_in_queue()

    def _download_worker(self, url: str, out_dir: str):
        try:
            ffmpeg_path = ensure_ffmpeg_available()
            if ffmpeg_path:
                format_selector = (
                    "bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/"
                    "bestvideo[height=720]+bestaudio/"
                    "best[height<=720]/best"
                )
            else:
                format_selector = (
                    "best[ext=mp4][acodec!=none][vcodec*=avc1][height<=720]/"
                    "best[acodec!=none][height<=720]/"
                    "best[acodec!=none]"
                )

            ydl_opts = {
                "quiet": True,
                "logger": QuietLogger(),
                "noplaylist": True,
                "progress_hooks": [self._download_hook],
                "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
                "format": format_selector,
                "windowsfilenames": True,
                "restrictfilenames": False,
                "concurrent_fragment_downloads": 4,
                "retries": 3,
            }
            if ffmpeg_path:
                ydl_opts["merge_output_format"] = "mp4"
                ydl_opts["ffmpeg_location"] = ffmpeg_path

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                self.current_title = info.get("title") or "video"

            final_title = sanitize_filename(self.current_title)
            candidate = self.last_downloaded_path
            if not candidate:
                with YoutubeDL({"quiet": True}) as y2:
                    candidate = y2.prepare_filename(info)

            if candidate and os.path.exists(candidate):
                base_dir = os.path.dirname(candidate)
                ext = os.path.splitext(candidate)[1] or ".mp4"
                target = os.path.join(base_dir, f"{final_title}{ext}")
                idx = 2
                while os.path.exists(target):
                    target = os.path.join(base_dir, f"{final_title}-{idx}{ext}")
                    idx += 1
                os.replace(candidate, target)
                self.root.after(0, self._set_status, f"Fini: {os.path.basename(target)}")
            else:
                self.root.after(0, self._set_status, "Téléchargement terminé.")

        except Exception as e:
            msg = str(e)
            if "ffmpeg" in msg.lower():
                self.root.after(
                    0,
                    messagebox.showerror,
                    "FFmpeg requis",
                    "FFmpeg est nécessaire pour fusionner audio/vidéo en 720p. Une tentative de téléchargement automatique a échoué.",
                )
            else:
                self.root.after(0, messagebox.showerror, "Erreur", msg[:1000])
        finally:
            self.root.after(0, self._after_item)


def main():
    root = tk.Tk()
    try:
        from tkinter import ttk as _ttk
        style = _ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    YouTubeDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
