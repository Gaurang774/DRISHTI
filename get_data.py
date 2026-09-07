"""
DRISHTI Data Acquisition Script
Run modes:
  python get_data.py --mode rdd2022    # Download RDD2022 India from Zenodo -> video
  python get_data.py --mode youtube    # Download Indian dashcam video
  python get_data.py --mode selfcheck  # Verify pipeline is ready
"""
import argparse, json, os, sys, urllib.request, zipfile
from pathlib import Path

RDD2022_URL   = "https://zenodo.org/record/7023004/files/India.zip"
YOUTUBE_URLS  = [
    ("https://www.youtube.com/watch?v=7J5fPfL-d_Y", "delhi_road.mp4"),
    ("https://www.youtube.com/watch?v=M3lHhgb6V58", "mumbai_road.mp4"),
]

def progress(count, block, total):
    pct = min(int(count * block * 100 / max(total, 1)), 100)
    bar = "=" * (pct // 5) + " " * (20 - pct // 5)
    print(f"\r  [{bar}] {pct}%", end="", flush=True)

def download_rdd2022():
    print(f"\n[DRISHTI] Downloading RDD2022 India subset (~420MB) from Zenodo...")
    try:
        urllib.request.urlretrieve(RDD2022_URL, "India.zip", reporthook=progress)
        print()
    except Exception as e:
        print(f"\n[ERROR] {e}"); return None
    print("[DRISHTI] Extracting...")
    Path("RDD2022_India").mkdir(exist_ok=True)
    with zipfile.ZipFile("India.zip") as z:
        z.extractall("RDD2022_India")
    Path("India.zip").unlink()
    img_dirs = list(Path("RDD2022_India").rglob("images"))
    return img_dirs[0] if img_dirs else None

def make_video(image_dir, out="rdd2022_demo.mp4", fps=10, limit=300):
    try: import cv2
    except ImportError:
        print("Run: pip install opencv-python"); return None
    imgs = sorted(Path(image_dir).glob("*.jpg"))[:limit]
    if not imgs: imgs = sorted(Path(image_dir).glob("*.png"))[:limit]
    if not imgs: print(f"No images in {image_dir}"); return None
    first = cv2.imread(str(imgs[0]))
    h, w = first.shape[:2]
    writer = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for i, p in enumerate(imgs):
        f = cv2.imread(str(p))
        if f is not None: writer.write(f)
    writer.release()
    print(f"[DRISHTI] Video created: {out} ({Path(out).stat().st_size//1024}KB, {len(imgs)} frames)")
    return out

def download_youtube(idx=0):
    try: import yt_dlp
    except ImportError:
        print("Run: pip install yt-dlp"); return None
    url, fname = YOUTUBE_URLS[idx]
    print(f"\n[DRISHTI] Downloading YouTube video: {url}")
    opts = {"format": "best[ext=mp4][height<=720]", "outtmpl": fname, "quiet": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    print(f"[DRISHTI] Saved: {fname}")
    return fname

def selfcheck():
    ok = True
    checks = {
        "detect.py": Path("detect.py").exists(),
        "drishti_api.py": Path("drishti_api.py").exists(),
        "Video files (*.mp4)": bool(list(Path(".").glob("*.mp4"))),
    }
    for label, result in checks.items():
        print(f"  {'OK' if result else 'MISSING'} | {label}")
        if not result: ok = False
    try:
        urllib.request.urlopen("http://localhost:8080/api/health", timeout=2)
        print("  OK | Backend at http://localhost:8080")
    except:
        print("  DOWN | Backend not running - start: python drishti_api.py"); ok = False
    if ok:
        vids = list(Path(".").glob("*.mp4"))
        print(f"\n  Ready: python detect.py --source {vids[0].name} --events events.jsonl")

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["rdd2022","youtube","selfcheck"], default="selfcheck")
ap.add_argument("--yt-index", type=int, default=0)
args = ap.parse_args()

if args.mode == "selfcheck": selfcheck()
elif args.mode == "rdd2022":
    d = download_rdd2022()
    if d:
        v = make_video(d)
        if v: print(f"\nRun: python detect.py --source {v} --events events.jsonl")
elif args.mode == "youtube":
    v = download_youtube(args.yt_index)
    if v: print(f"\nRun: python detect.py --source {v} --events events.jsonl")
