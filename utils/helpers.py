import os
import re
from typing import Optional

def is_valid_youtube_url(url: str) -> bool:
    """
    YouTube URL'sinin geçerliliğini kontrol et
    
    Args:
        url: Kontrol edilecek URL
    
    Returns:
        True eğer geçerliyse, False değilse
    """
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/',
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/embed/[\w-]+',
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url):
            return True
    
    return False

def cleanup_file(file_path: Optional[str]) -> bool:
    """
    Geçici dosyayı sil
    
    Args:
        file_path: Silinecek dosyanın yolu
    
    Returns:
        True eğer başarılıysa, False değilse
    """
    if not file_path:
        return False
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Dosya silindi: {file_path}")
            return True
        else:
            print(f"Dosya bulunamadı: {file_path}")
            return False
    except Exception as e:
        print(f"Dosya silme hatası: {e}")
        return False

def format_file_size(size_bytes: int) -> str:
    """
    Dosya boyutunu okunabilir formata çevir
    
    Args:
        size_bytes: Byte cinsinden dosya boyutu
    
    Returns:
        Okunabilir format (örn: "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def sanitize_filename(filename: str) -> str:
    """
    Dosya adını güvenli hale getir
    
    Args:
        filename: Orijinal dosya adı
    
    Returns:
        Güvenli dosya adı
    """
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    filename = filename.strip()
    
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def get_download_folder() -> str:
    """
    İndirme klasörünün yolunu al, yoksa oluştur
    
    Returns:
        İndirme klasörünün tam yolu
    """
    download_folder = 'downloads'
    
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    return download_folder

def cleanup_old_files(folder: str = 'downloads', max_age_hours: int = 1) -> int:
    """
    Eski dosyaları temizle
    
    Args:
        folder: Temizlenecek klasör
        max_age_hours: Maksimum dosya yaşı (saat)
    
    Returns:
        Silinen dosya sayısı
    """
    import time
    
    if not os.path.exists(folder):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    try:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Eski dosya silindi: {filename}")
    
    except Exception as e:
        print(f"Dosya temizleme hatası: {e}")
    
    return deleted_count
