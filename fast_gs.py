import subprocess
import os
import multiprocessing

def compress_pdf_turbo(input_file, output_file, gs_path=None):
    if gs_path is None:
        if os.name == 'nt':
            # List kemungkinan path Ghostscript
            possible_paths = [
                r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe",
                r"C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe",
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    gs_path = p
                    break
    
    if not gs_path or not os.path.exists(gs_path):
        print("❌ Error: Ghostscript tidak ketemu.")
        return False

    # Deteksi jumlah core CPU biar maksimal
    cpu_cores = multiprocessing.cpu_count()
    
    print(f"🚀 Turbo Mode ON: Menggunakan {cpu_cores} Threads CPU")
    print(f"🔧 Engine: {gs_path}")
    
    command = [
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/ebook", 
        "-dNOPAUSE", 
        "-dQUIET", 
        "-dBATCH",
        
        # --- SPEED TWEAKS ---
        f"-dNumRenderingThreads={cpu_cores}", # Pakai semua otak CPU
        "-dColorImageDownsampleType=/Average", # Ganti Bicubic (berat) jadi Average (ringan)
        "-dGrayImageDownsampleType=/Average",
        "-dMonoImageDownsampleType=/Average",
        "-dOptimize=true",                     # Optimasi struktur file
        # --------------------

        "-dColorImageResolution=150",
        "-dGrayImageResolution=150",
        "-dMonoImageResolution=150",
        f"-sOutputFile={output_file}",
        input_file
    ]

    try:
        subprocess.run(command, check=True)
        
        if os.path.exists(output_file):
            old_size = os.path.getsize(input_file) / (1024 * 1024)
            new_size = os.path.getsize(output_file) / (1024 * 1024)
            print("-" * 30)
            print(f"✅ Selesai!")
            print(f"📉 Size: {old_size:.2f} MB -> {new_size:.2f} MB")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Pastikan file input ada
    compress_pdf_turbo("input.pdf", "output_turbo.pdf")