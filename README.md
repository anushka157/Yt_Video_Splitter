# 🎬 YouTube Video Splitter

A Python tool to split videos for **YouTube Shorts**, **Instagram Reels**, and **TikTok** with customizable splits, portrait cropping, and watermarking.

---

## ✅ Features

- Split videos by equal duration or at specific timestamps
- Convert to portrait mode for mobile-first platforms
- Crop content to fit vertical aspect ratio
- Add customizable text watermark (font, size, color)
- Automatically organize output files into a directory

---

## 🛠 Requirements

- Python 3.13.5  
- FFmpeg (included in repo or install manually)  
- Python dependencies listed in `requirements.txt`

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/yt-video-splitter.git
cd yt-video-splitter
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. FFmpeg Installation
- If FFmpeg is not pre-included:

- Visit: https://www.gyan.dev/ffmpeg/builds/

- Download: ffmpeg-git-full.7z

- Extract the archive using 7-Zip or similar

- Add the extracted bin folder to your system's PATH
  or place ffmpeg.exe in your project directory

# 📂 Output
- All processed clips will be saved in the directory specified using --output-dir

- If no output directory is specified, it defaults to ./output

# 🤝 Contributing
- Found a bug or have a feature request?
- Feel free to fork this repo and open a pull request!

# 📬 Contact
- For questions or suggestions, feel free to open an issue on GitHub.
