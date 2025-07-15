import os
import subprocess
import argparse

FFMPEG_DIR = os.path.join(os.getcwd(), "ffmpeg", "bin")
FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(FFMPEG_DIR, "ffprobe.exe")

def validate_ffmpeg():
    if not os.path.isfile(FFMPEG_PATH):
        print(f"Error: FFmpeg not found at {FFMPEG_PATH}")
        exit(1)

def get_video_duration(input_video):
    """Get video duration in seconds using ffprobe"""
    cmd = [FFPROBE_PATH, '-v', 'error', '-show_entries', 
           'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
           input_video]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting duration: {str(e)}")
        return None

def parse_time(time_str):
    """Convert time string to seconds (supports HH:MM:SS or seconds)"""
    try:
        if ':' in time_str:
            parts = list(map(float, time_str.split(':')))
            if len(parts) == 3:
                return parts[0]*3600 + parts[1]*60 + parts[2]
            elif len(parts) == 2:
                return parts[0]*60 + parts[1]
            else:
                raise ValueError("Invalid time format")
        return float(time_str)
    except ValueError:
        print(f"Invalid time format: {time_str}")
        return None

def build_aspect_filter(aspect):
    """Generate FFmpeg filter for desired aspect ratio with safe scaling"""
    if aspect == 'portrait':
        return (
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    elif aspect == 'landscape':
        return (
            "scale=1920:1080:force_original_aspect_ratio=decrease,"
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black"
        )
    return None

def split_video_segment(input_path, output_path, start=None, duration=None, aspect='original'):
    """Build and execute FFmpeg command for a single segment"""
    cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error']
    
    if start is not None:
        cmd += ['-ss', str(start)]
    
    cmd += ['-i', input_path]
    
    filter_str = build_aspect_filter(aspect)
    if filter_str:
        cmd += [
            '-vf', filter_str,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-movflags', '+faststart',
            '-x264-params', 'vbv-bufsize=8000:vbv-maxrate=5000'
        ]
    else:
        cmd += ['-c:v', 'copy']
    
    cmd += ['-c:a', 'aac', '-b:a', '128k']
    
    if duration is not None:
        cmd += ['-t', str(duration)]
    
    cmd.append(output_path)
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr}")
        return False

def main():
    validate_ffmpeg()
    
    parser = argparse.ArgumentParser(description='Video Splitter with Aspect Ratio Control')
    parser.add_argument('input_video', help='Path to input video file')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    parser.add_argument('--split-option', choices=['60', 'custom'], required=True,
                      help='Split mode: 60-second segments or custom times')
    parser.add_argument('--split-times', nargs='+', help='Custom split times in seconds or HH:MM:SS')
    parser.add_argument('--aspect', choices=['portrait', 'landscape', 'original'], default='original',
                      help='Output aspect ratio')
    
    args = parser.parse_args()

    # Validate input file
    if not os.path.isfile(args.input_video):
        print(f"Input file not found: {args.input_video}")
        return

    # Create output directory
    base_name = os.path.splitext(os.path.basename(args.input_video))[0]
    output_folder = os.path.join(args.output_dir, base_name)
    os.makedirs(output_folder, exist_ok=True)

    # Handle 60-second split
    if args.split_option == '60':
        print("Processing 60-second segments...")
        if args.aspect == 'original':
            # Fast split using stream copy
            cmd = [
                FFMPEG_PATH, '-y', '-i', args.input_video,
                '-f', 'segment', '-segment_time', '60',
                '-reset_timestamps', '1', '-c', 'copy',
                os.path.join(output_folder, f"{base_name}_%03d.mp4")
            ]
            try:
                subprocess.run(cmd, check=True)
                print("60-second segments created successfully")
            except subprocess.CalledProcessError as e:
                print(f"Segment split failed: {e}")
        else:
            # Re-encode with aspect ratio
            duration = get_video_duration(args.input_video)
            if not duration:
                return
            
            segment_count = int(duration // 60) + (1 if duration % 60 > 0 else 0)
            for i in range(segment_count):
                start = i * 60
                output_path = os.path.join(output_folder, f"{base_name}_{i+1:03d}.mp4")
                success = split_video_segment(
                    args.input_video, output_path,
                    start=start, duration=60, aspect=args.aspect
                )
                if not success:
                    return
            print(f"Created {segment_count} 60-second segments")
        return

    # Handle custom split
    if not args.split_times:
        print("Error: Custom split requires --split-times")
        return
    
    # Parse and validate split times
    split_points = []
    for t in args.split_times:
        parsed = parse_time(t)
        if parsed is None:
            return
        split_points.append(parsed)
    
    duration = get_video_duration(args.input_video)
    if not duration:
        return
    
    split_points = sorted([0] + [p for p in split_points if 0 < p < duration] + [duration])
    segments = []
    for i in range(len(split_points) - 1):
        start = split_points[i]
        end = split_points[i+1]
        if end - start > 0.1:  # Minimum segment duration 0.1 seconds
            segments.append((start, end - start))
    
    if not segments:
        print("No valid segments created")
        return
    
    print(f"Creating {len(segments)} custom segments...")
    for idx, (start, length) in enumerate(segments, 1):
        output_path = os.path.join(output_folder, f"{base_name}_part{idx}.mp4")
        print(f"Processing segment {idx}: {start:.1f}s - {start+length:.1f}s")
        success = split_video_segment(
            args.input_video, output_path,
            start=start, duration=length, aspect=args.aspect
        )
        if not success:
            return
    
    print("All segments created successfully")

if __name__ == "__main__":
    main()
