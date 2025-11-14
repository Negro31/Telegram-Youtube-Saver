import os
import yt_dlp
import asyncio
from typing import Optional, Dict

DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

async def get_video_info(url: str) -> Optional[Dict]:
    """Video bilgilerini al"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        loop = asyncio.get_event_loop()
        
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        info = await loop.run_in_executor(None, extract_info)
        
        return {
            'title': info.get('title'),
            'duration': info.get('duration'),
            'duration_string': info.get('duration_string'),
            'uploader': info.get('uploader'),
        }
    except Exception as e:
        print(f"Video bilgisi alma hatası: {e}")
        return None

async def download_video(url: str, format_type: str, quality: str) -> Optional[str]:
    """
    YouTube videosunu indir
    
    Args:
        url: YouTube video URL'si
        format_type: mp4, mp3, audio, video
        quality: 360, 480, 720, 1080, 1440, 2160, 128, 192, 320, m4a, webm
    
    Returns:
        İndirilen dosyanın yolu veya None
    """
    try:
        output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s_%(id)s.%(ext)s')
        
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
        }
        
        if format_type == 'mp4':
            height = quality
            ydl_opts['format'] = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            
        elif format_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }]
            
        elif format_type == 'audio':
            if quality == 'm4a':
                ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
            elif quality == 'webm':
                ydl_opts['format'] = 'bestaudio[ext=webm]/bestaudio/best'
            else:
                ydl_opts['format'] = 'bestaudio/best'
                
        elif format_type == 'video':
            ydl_opts['format'] = 'bestvideo[ext=mp4]/bestvideo/best'
        
        else:
            ydl_opts['format'] = 'best'
        
        loop = asyncio.get_event_loop()
        
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if format_type == 'mp3':
                    filename = ydl.prepare_filename(info)
                    base_filename = os.path.splitext(filename)[0]
                    return f"{base_filename}.mp3"
                else:
                    return ydl.prepare_filename(info)
        
        file_path = await loop.run_in_executor(None, download)
        
        if os.path.exists(file_path):
            return file_path
        
        possible_files = [
            file_path,
            file_path.replace('.webm', '.mp3'),
            file_path.replace('.m4a', '.mp3'),
            file_path.replace('.opus', '.mp3'),
        ]
        
        for pf in possible_files:
            if os.path.exists(pf):
                return pf
        
        download_dir_files = os.listdir(DOWNLOAD_FOLDER)
        if download_dir_files:
            latest_file = max(
                [os.path.join(DOWNLOAD_FOLDER, f) for f in download_dir_files],
                key=os.path.getctime
            )
            if os.path.exists(latest_file):
                return latest_file
        
        return None
        
    except Exception as e:
        print(f"İndirme hatası: {e}")
        return None
