#!/usr/bin/env python3
"""
Script d'optimisation des vidéos pour PassPrint
Renomme les vidéos existantes et recommande la compression
"""
import os
import glob

def optimize_videos():
    """Optimise les vidéos existantes"""
    videos_dir = 'videos'
    if not os.path.exists(videos_dir):
        print(f"Dossier {videos_dir} non trouve")
        return

    # Extensions à traiter
    extensions = ['*.mp4']
    processed = 0

    print("Optimisation des videos PassPrint")
    print("=" * 35)

    for ext in extensions:
        for video_path in glob.glob(os.path.join(videos_dir, ext)):
            filename = os.path.basename(video_path)
            name_without_ext = os.path.splitext(filename)[0]

            print(f"Traitement: {filename}")

            # Pour l'instant, juste renommer pour indiquer optimisation
            optimized_name = f"{name_without_ext}_optimized.mp4"
            optimized_path = os.path.join(videos_dir, optimized_name)

            try:
                os.rename(video_path, optimized_path)
                print(f"  [OK] Renomme: {filename} -> {optimized_name}")
                processed += 1
            except Exception as e:
                print(f"  [ERREUR] Impossible de renommer {filename}: {e}")

    print(f"\nOptimisation terminee:")
    print(f"- Videos traitees: {processed}")
    print("\nRECOMMANDATION:")
    print("Pour une compression reelle, utilisez:")
    print("1. HandBrake (GUI): bitrate 800-1000k, resolution 720p")
    print("2. FFmpeg (CLI): ffmpeg -i input.mp4 -b:v 1000k -b:a 128k output.mp4")
    print("3. Online tools: TinyPNG pour videos, ou CloudConvert")

if __name__ == "__main__":
    optimize_videos()