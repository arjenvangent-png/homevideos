#!/usr/bin/env python3
"""
Homevideo merger - FFmpeg versie (betrouwbaarder op Windows)
Voegt video's samen zonder MoviePy
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

def get_video_files(folder_path):
    """Haalt alle videobestanden recursief op (gesorteerd op pad, zodat datummappen chronologisch blijven)"""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.m2ts', '.mts', '.ts', '.mpg'}
    videos = []

    for file in sorted(Path(folder_path).rglob('*')):
        if file.is_file() and file.suffix.lower() in video_extensions:
            videos.append(file)

    if not videos:
        print(f"❌ Geen videobestanden gevonden in {folder_path} (ook niet in submappen)")
        sys.exit(1)

    print(f"✓ Gevonden: {len(videos)} videobestanden")
    for v in videos:
        print(f"  - {v.relative_to(folder_path)}")
    return videos
 
def check_ffmpeg():
    """Controleer of FFmpeg geïnstalleerd is"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ FFmpeg niet gevonden!")
        print("Installeer FFmpeg: winget install ffmpeg")
        sys.exit(1)
 
def validate_video(video_file):
    """Controleer of een videobestand een videostream heeft (via ffprobe, niet decoderen)"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_type',
            '-of', 'csv=p=0',
            str(video_file)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=10, text=True)
        return result.returncode == 0 and 'video' in result.stdout
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False
 
def merge_videos(folder_path, output_name="merged_video.mp4"):
    """Voegt videos samen met FFmpeg in twee fases (robuust voor corrupte audio)"""

    check_ffmpeg()
    all_video_files = get_video_files(folder_path)

    # Valideer videos (alleen check op videostream aanwezigheid)
    print(f"\n🔍 Video's valideren...")
    valid_videos = []
    skipped_videos = []

    for video_file in all_video_files:
        print(f"  {video_file.name}...", end=" ", flush=True)
        if validate_video(video_file):
            print("✓")
            valid_videos.append(video_file)
        else:
            print("❌ OVERGESLAGEN (geen videostream gevonden)")
            skipped_videos.append(video_file.name)

    if not valid_videos:
        print("❌ Geen geldige video's gevonden!")
        sys.exit(1)

    if skipped_videos:
        print(f"\n⚠️  {len(skipped_videos)} bestand(en) overgeslagen:")
        for name in skipped_videos:
            print(f"  - {name}")

    temp_dir = tempfile.mkdtemp(prefix="videomerge_")
    temp_files = []

    try:
        # --- Fase 1: elk bestand individueel converteren ---
        # Fout-tolerante flags werken hier wél correct (per bestand, niet via concat demuxer)
        # stderr wordt onderdrukt zodat AC3-ruis niet de console vervuilt
        print(f"\n🔄 Fase 1: {len(valid_videos)} bestanden converteren...")
        print(f"⚠️  Re-encoding naar H.264 (dit kan even duren - tijd voor koffie ☕)...")

        for i, video_file in enumerate(valid_videos, 1):
            temp_out = os.path.join(temp_dir, f"temp_{i:04d}.mp4")
            print(f"  [{i}/{len(valid_videos)}] {video_file.name}...", end=" ", flush=True)

            cmd = [
                'ffmpeg',
                '-fflags', '+genpts+discardcorrupt',
                '-err_detect', 'ignore_err',
                '-i', str(video_file),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '18',
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '48000',
                '-ac', '2',
                '-y',
                temp_out
            ]

            result = subprocess.run(cmd, capture_output=True)  # stderr onderdrukt

            if result.returncode == 0:
                print("✓")
                temp_files.append(temp_out)
            else:
                print(f"❌ mislukt, overgeslagen")
                skipped_videos.append(video_file.name)

        if not temp_files:
            print("❌ Geen enkel bestand kon worden geconverteerd!")
            sys.exit(1)

        # --- Fase 2: schone bestanden samenvoegen met stream-copy (geen decode, geen errors) ---
        print(f"\n📹 Fase 2: {len(temp_files)} geconverteerde bestanden samenvoegen...")

        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                escaped = temp_file.replace("\\", "/").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',   # Stream copy: razendsnel, geen hercodering
            '-y',
            output_name
        ]

        result = subprocess.run(cmd, capture_output=False)

        if result.returncode == 0:
            print(f"\n✓ Klaar! Video opgeslagen: {output_name}")
            if skipped_videos:
                print(f"   ({len(temp_files)} van {len(all_video_files)} bestanden gebruikt)")
        else:
            print(f"\n❌ FFmpeg fout bij samenvoegen (code: {result.returncode})")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Fout: {e}")
        sys.exit(1)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
 
def main():
    if len(sys.argv) < 2:
        print("Gebruik: python video_merger_ffmpeg.py C:\\pad\\naar\\videomap [output.mp4]")
        print("\nVoorbeeld:")
        print('  python video_merger_ffmpeg.py "C:\\Users\\JouwNaam\\Videos\\vakantie"')
        print('  python video_merger_ffmpeg.py "C:\\Users\\JouwNaam\\Videos\\vakantie" vakantie.mp4')
        sys.exit(1)
    
    folder_path = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "merged_video.mp4"
    
    if not os.path.isdir(folder_path):
        print(f"❌ Map niet gevonden: {folder_path}")
        sys.exit(1)
    
    print(f"🎬 Video Merger (FFmpeg)")
    print(f"Bronmap: {folder_path}")
    print(f"Output: {output_name}\n")
    
    merge_videos(folder_path, output_name)
 
if __name__ == "__main__":
    main()