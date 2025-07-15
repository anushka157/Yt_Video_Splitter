import os
import subprocess
import argparse

FFMPEG_DIR = os.path.join(os.getcwd(), "ffmpeg", "bin")
FFMPEG_PATH = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE_PATH = os.path.join(FFMPEG_DIR, "ffprobe.exe")

def validate_environment():
    if not all(os.path.isfile(p) for p in [FFMPEG_PATH, FFPROBE_PATH]):
        print("Error: FFmpeg binaries not found!")
        exit(1)

def get_video_duration(input_path):
    cmd = [FFPROBE_PATH, '-v', 'error', '-show_entries', 
          'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', 
          input_path]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting duration: {str(e)}")
        return None

def build_filters(args):
    # Set target dimensions based on aspect mode
    if args.aspect_mode == 'portrait':
        target_width, target_height = 1080, 1920
    else:  # landscape
        target_width, target_height = 1920, 1080

    filters = []
    
    # Handle aspect conversion
    if args.aspect_handling == 'crop':
        filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase")
        filters.append(f"crop={target_width}:{target_height}")
    elif args.aspect_handling == 'pad':
        filters.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease")
        bg_color = args.background if args.background else 'black'
        filters.append(f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={bg_color}")
    elif args.aspect_handling == 'stretch':
        filters.append(f"scale={target_width}:{target_height}")
    else:  # original
        return None

    # Add text overlay
    if args.text:
        text_color = args.text_color or ('white' if args.background == 'black' else 'black')
        font = f":fontfile='{args.font}'" if args.font else ''
        filters.append(
            f"drawtext=text='{args.text}'{font}:"
            f"fontcolor={text_color}:fontsize={args.text_size}:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        )
    
    return ','.join(filters)

def process_segment(input_path, output_path, start=None, duration=None, args=None):
    cmd = [FFMPEG_PATH, '-y', '-hide_banner', '-loglevel', 'error']
    
    if start is not None:
        cmd += ['-ss', str(start)]
    
    cmd += ['-i', input_path]
    
    filters = build_filters(args)
    if filters:
        cmd += [
            '-vf', filters,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-movflags', '+faststart'
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
        print(f"Error processing segment: {e.stderr}")
        return False

def main():
    validate_environment()
    
    parser = argparse.ArgumentParser(description='Video Splitter with Text Overlay')
    parser.add_argument('input', help='Input video file path')
    parser.add_argument('--split-option', choices=['60', 'custom'], required=True,
                      help='Split mode: 60-second segments or custom times')
    parser.add_argument('--split-times', nargs='+', 
                      help='Custom split times in seconds or HH:MM:SS format')
    parser.add_argument('--output-dir', default='output', help='Output directory')
    
    # Aspect ratio options
    parser.add_argument('--aspect-mode', choices=['portrait', 'landscape'], required=True,
                      help='Target aspect ratio orientation')
    parser.add_argument('--aspect-handling', choices=['pad', 'crop', 'stretch', 'original'],
                      default='pad', help='How to handle aspect ratio conversion')
    parser.add_argument('--background', choices=['black', 'white'], 
                      default='black', help='Padding background color')
    
    # Text options
    parser.add_argument('--text', help='Text to display on padding area')
    parser.add_argument('--text-size', type=int, default=48,
                      help='Text font size')
    parser.add_argument('--text-color', help='Text color (default: white/black based on background)')
    parser.add_argument('--font', help='Path to custom font file')
    
    args = parser.parse_args()

    # Validate input file
    if not os.path.isfile(args.input):
        print(f"Input file not found: {args.input}")
        return

    # Create output directory
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    output_folder = os.path.join(args.output_dir, base_name)
    os.makedirs(output_folder, exist_ok=True)
    print(f"Output directory: {output_folder}")

    # Handle 60-second split
    if args.split_option == '60':
        print("Processing 60-second segments...")
        duration = get_video_duration(args.input)
        if duration is None:
            return
        
        segment_count = int(duration // 60) + (1 if duration % 60 > 0 else 0)
        for i in range(segment_count):
            start = i * 60
            seg_duration = min(60, duration - start)
            output_path = os.path.join(output_folder, f"{base_name}_{i+1:03d}.mp4")
            print(f"Processing segment {i+1}/{segment_count}")
            process_segment(args.input, output_path, start=start, 
                          duration=seg_duration, args=args)
        print("Processing completed")
        return

    # Handle custom split (implementation similar to previous versions)

if __name__ == "__main__":
    main()
