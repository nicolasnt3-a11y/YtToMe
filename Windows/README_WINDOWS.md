# YT to me (Windows) — Build et utilisation

Version Windows autonome (GUI) pour télécharger des vidéos YouTube en 720p.

## Contenu
- `app_win.py`: application GUI (multi-URLs, icône PNG optionnelle, marquage vert + check).
- `requirements.txt`: dépendances.
- `build.bat`: script pour créer un exécutable Windows (onefile, sans console).

## Prérequis
- Windows 10/11
- Python 3.9+ installé et accessible dans PATH

## Construction de l'exécutable
1. Ouvrez l'Explorateur dans ce dossier `Windows/`.
2. Double-cliquez `build.bat` (ou exécutez dans PowerShell):
   ```powershell
   ./build.bat
   ```
3. Le script installe les dépendances, génère `dist/YT-to-me.exe`.
4. Si un PNG est présent dans ce dossier, il sert d'icône pour l'EXE.


## FFmpeg automatique
- L'app cherche `ffmpeg.exe` à côté de l'EXE, dans le PATH, ou télécharge un binaire via `imageio-ffmpeg` lors de l'exécution.
- Pour un fonctionnement garanti hors-ligne, vous pouvez copier `ffmpeg.exe` dans `Windows/dist/` après la construction.

## Utilisation
1. Lancez `dist/YT-to-me.exe`.
2. Collez une ou plusieurs URLs YouTube, **une par ligne**.
3. Choisissez le dossier de téléchargement.
4. Cliquez « Télécharger en 720p ».
5. Chaque URL est traitée séquentiellement; la ligne devient verte avec un check quand c'est terminé.

## Notes
- La 720p est utilisée quand les flux sont disponibles. Sinon, meilleur ≤720p.
- Les fichiers sont nommés d'après le titre, normalisé (sans accents, sans caractères spéciaux, sans espaces).
