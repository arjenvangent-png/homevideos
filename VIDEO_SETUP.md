# Video Merger - Setup & Gebruikshandleiding

## Stap 1: Dependencies installeren

MoviePy + FFmpeg nodig. Kies je OS:

### macOS
```bash
brew install ffmpeg
pip install moviepy
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install ffmpeg
pip install moviepy
```

### Windows
1. Download FFmpeg van https://ffmpeg.org/download.html
2. Zet in je PATH of installeer via winget:
   ```bash
   winget install ffmpeg
   ```
3. pip install moviepy
   ```bash
   pip install moviepy
   ```

## Stap 2: Script uitvoeren

```bash
# Basis gebruik
python video_merger.py /pad/naar/je/videomap

# Met custom output naam
python video_merger.py /pad/naar/je/videomap output_familiefilm.mp4
```

### Voorbeelden:

**macOS/Linux:**
```bash
python video_merger.py ~/Videos/vakantie2024
python video_merger.py ~/Videos/vakantie2024 vakantie_samengesteld.mp4
```

**Windows:**
```bash
python video_merger.py "C:\Users\JouwNaam\Videos\vakantie2024"
python video_merger.py "C:\Users\JouwNaam\Videos\vakantie2024" vakantie.mp4
```

## Wat doet het script:

1. Leest alle videobestanden uit je map (alfabetisch gesorteerd)
2. Voegt ze aan elkaar met 1 seconde fade transitions
3. Exporteert als MP4 met H.264 codec
4. Output staat in dezelfde map waar je het script uitvoert

## Output locatie aanpassen

Wil je de output naar een specifieke map schrijven? Pas het script aan:

In de `main()` functie, vervang:
```python
output_name = sys.argv[2] if len(sys.argv) > 2 else "merged_video.mp4"
```

Door bijv:
```python
output_name = os.path.expanduser("~/Videos/merged_video.mp4")
```

## Ondersteunde videoformaten

- MP4, MOV, AVI, MKV, FLV, WMV, WebM

## Opties aanpassen

In het script kan je wijzigen:
- `transition_duration=1` → duur van fade effect (in seconden)
- `codec='libx264'` → videokwaliteit (libx264 = goed voor web)
- `audio_codec='aac'` → audio format

## Troubleshooting

**"FFmpeg not found"**
→ FFmpeg niet geïnstalleerd. Volg stap 1 opnieuw.

**"No module named 'moviepy'"**
→ pip install moviepy niet gedaan

**Video's encoden duurt erg lang**
→ Dit is normaal. Hangt af van je video duur en computer. Wacht of pak een koffie.

**Getekende video is zwart**
→ Codec-issue. Probeer transcode-settings aan te passen of gebruik DaVinci Resolve (gratis) in plaats daarvan.
