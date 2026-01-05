import subprocess
import os
import sys

def compress_pdf_ghostscript(input_file, output_file, gs_path=None):
    # 1. Deteksi Path Ghostscript
    # Kalau gs_path tidak diisi, kita coba tebak lokasi default Windows
    if gs_path is None:
        if os.name == 'nt': # Windows
            # Cek folder instalasi umum (sesuaikan versimu jika beda)
            possible_paths = [
                r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe", # Versi terbaru
                r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
                r"C:\Program Files\gs\gs9.56.1\bin\gswin64c.exe",
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    gs_path = p
                    break
            
            if gs_path is None:
                print("❌ Error: Ghostscript (.exe) tidak ditemukan di lokasi standar.")
                print("   Silakan edit variabel 'gs_executable' di dalam script.")
                return False
        else: # Linux / Mac
            gs_path = "gs" # Biasanya sudah ada di PATH

    print(f"🔧 Menggunakan Ghostscript di: {gs_path}")
    print(f"📄 Memproses: {input_file} -> {output_file}")

    # 2. Susun Command (Command Sakti)
    # Settingan ini setara 'Recommended' compression di iLovePDF (150 DPI)
    command = [
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook",       # Kualitas Medium (150 dpi), ganti /screen jika mau low (72 dpi)
        "-dNOPAUSE", 
        "-dQUIET", 
        "-dBATCH",
        "-dColorImageDownsampleType=/Average", # Resampling halus
        "-dColorImageResolution=150",          # Target resolusi gambar
        "-dGrayImageResolution=150",
        "-dMonoImageResolution=150",
        f"-sOutputFile={output_file}",
        input_file
    ]

    # 3. Eksekusi
    try:
        # shell=False lebih aman, kita panggil executable langsung
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Cek hasil size
        if os.path.exists(output_file):
            old_size = os.path.getsize(input_file) / (1024 * 1024)
            new_size = os.path.getsize(output_file) / (1024 * 1024)
            print("-" * 30)
            print(f"✅ Sukses! PDF berhasil ditulis ulang.")
            print(f"📉 Size: {old_size:.2f} MB -> {new_size:.2f} MB")
            return True
        else:
            print("❌ Gagal: File output tidak terbentuk.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Error saat menjalankan Ghostscript: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: Executable Ghostscript tidak ditemukan/salah path.")
        return False

if __name__ == "__main__":
    # GANTI PATH INI SESUAI LOKASI GHOSTSCRIPT DI PC KAMU
    # Kalau sudah diinstall di default C:\Program Files\gs\gs10.04.0\..., script akan coba cari otomatis.
    # Tapi kalau beda, isi path manual di bawah:
    custom_gs_path = None  # Contoh: r"D:\Apps\Ghostscript\bin\gswin64c.exe"

    input_pdf = "input.pdf"
    output_pdf = "output_gs.pdf"

    if os.path.exists(input_pdf):
        compress_pdf_ghostscript(input_pdf, output_pdf, gs_path=custom_gs_path)
    else:
        print(f"File {input_pdf} tidak ditemukan!")