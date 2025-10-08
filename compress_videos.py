#!/usr/bin/env python3
"""
Script de compression des vidéos pour PassPrint
Utilise moviepy pour compresser les MP4
"""
import os
import glob
from moviepy import VideoFileClip

def compress_video(input_path, output_path, target_bitrate='1000k'):
    """Compresse une vidéo avec le bitrate spécifié"""
    try:
        print(f"Compression de {os.path.basename(input_path)}...")

        # Charger la vidéo
        clip = VideoFileClip(input_path)

        # Compresser avec paramètres optimisés
        clip.write_videofile(
            output_path,
            bitrate=target_bitrate,
            audio_bitrate='128k',
            preset='medium',
            threads=4
        )

        clip.close()
        return True

    except Exception as e:
        print(f"Erreur compression {input_path}: {e}")
        return False

def process_videos():
    """Traite toutes les vidéos du dossier videos/"""
    videos_dir = 'videos'
    if not os.path.exists(videos_dir):
        print(f"Dossier {videos_dir} non trouve")
        return

    # Créer dossier pour les vidéos compressées
    compressed_dir = os.path.join(videos_dir, 'compressed')
    os.makedirs(compressed_dir, exist_ok=True)

    # Extensions à traiter
    extensions = ['*.mp4']
    processed = 0
    compressed = 0

    # Pour le test, traiter seulement la première vidéo
    test_mode = True
    max_videos = 1 if test_mode else float('inf')

    for ext in extensions:
        for video_path in glob.glob(os.path.join(videos_dir, ext)):
            if processed >= max_videos:
                break

            filename = os.path.basename(video_path)
            name_without_ext = os.path.splitext(filename)[0]

            print(f"Traitement: {filename}")

            # Compresser la vidéo
            compressed_path = os.path.join(compressed_dir, f"{name_without_ext}_compressed.mp4")
            if compress_video(video_path, compressed_path, target_bitrate='800k'):
                compressed += 1
                print(f"  [OK] Compresse: {filename}")

            processed += 1

    print(f"\nTraitement termine:")
    print(f"- Videos traitees: {processed}")
    print(f"- Videos compressees: {compressed}")
    if test_mode:
        print("NOTE: Mode test - seulement 1 video traitee")

if __name__ == "__main__":
    print("Compression des videos PassPrint")
    print("=" * 35)
    process_videos()
    print("\nCompression terminee!")