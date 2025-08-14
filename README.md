## YT to me — Téléchargeur YouTube 720p (GUI)

<img width="732" height="462" alt="yttome" src="https://github.com/user-attachments/assets/dc78be6c-1dfd-4f62-8248-621b75a3831a" />


Application locale en Python (Tkinter) pour télécharger une ou plusieurs vidéos YouTube en 720p via une interface graphique simple, sans utiliser la ligne de commande.

### Installation

- **Prérequis**: Python 3.9+ avec Tkinter.
- Ouvrez ce dossier dans votre IDE ou l’Explorateur.

1. (Optionnel mais recommandé) Créez un environnement virtuel:
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
2. Installez les dépendances:
   ```bash
   pip install -r requirements.txt
   ```

### Lancer l’application (sans console)

- Double-cliquez sur `app.py` (selon votre association de fichiers, une console peut s’ouvrir).
- Pour éviter toute console sur Windows, lancez avec `pythonw`:
  ```powershell
  pythonw app.py
  ```

### FFmpeg automatique (application autonome)

- L’application tente de trouver `ffmpeg` automatiquement:
  - À côté de `app.py` (`ffmpeg.exe`/`ffmpeg`)
  - Dans le `PATH` système
  - Sinon, elle télécharge un binaire via `imageio-ffmpeg` et le copie à côté de `app.py`
- Avec FFmpeg disponible, la **fusion audio/vidéo** est assurée et vous obtenez la **720p** quand YouTube fournit le flux.
- Si tout échoue, l’app bascule en « flux progressif ≤720p » (sans FFmpeg), ce qui peut être de qualité inférieure.

### Utilisation (multi-URLs)

1. Collez une ou plusieurs URLs YouTube, **une par ligne**.
2. Choisissez le dossier de téléchargement (par défaut: `Téléchargements`).
3. Cliquez sur « Télécharger en 720p ».
4. Les vidéos seront téléchargées **séquentiellement**, dans l’ordre des lignes.
5. Chaque fichier est nommé d’après le titre, normalisé (sans accents, sans caractères spéciaux, sans espaces).

### Générer un exécutable (optionnel)

Avec PyInstaller (non inclus par défaut):
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "YT-to-me" app.py
```
L’exécutable sera disponible dans `dist/`.

### Remarques

- L’application ne lit pas automatiquement des playlists; collez les liens des vidéos souhaitées, une par ligne.
- Sortie: MP4 quand fusionné, sinon extension du flux téléchargé.
