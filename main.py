import fitz  # PyMuPDF
from PIL import Image
import io
import os

# --- KONFIGURASI MODERAT ---
# Kualitas JPEG (0-100). 75 adalah sweet spot antara ukuran dan kualitas visual.
# Jangan di bawah 60 kalau tidak mau burik.
JPEG_QUALITY = 75 

# Dimensi maksimum (lebar atau tinggi). 
# 1500px biasanya cukup tajam untuk dokumen standar A4 di layar.
# Kalau masih terlalu besar, turunkan ke 1200 atau 1000.
MAX_DIMENSION = 1500 
# ---------------------------

def resize_and_compress_image(image_bytes):
    """
    Fungsi helper untuk memproses satu gambar:
    1. Baca bytes gambar dengan Pillow.
    2. Handle transparansi (agar tidak jadi hitam).
    3. Resize jika terlalu besar.
    4. Simpan sebagai JPEG.
    """
    try:
        # Load gambar dari bytes
        img_pil = Image.open(io.BytesIO(image_bytes))
        
        # --- LANGKAH KRUSIAL: Handle Transparansi ---
        # Jika gambar punya alpha channel (RGBA) atau palette (P),
        # convert ke RGB dengan background PUTIH. Kalau langsung convert ke RGB,
        # area transparan akan jadi HITAM.
        if img_pil.mode in ('RGBA', 'LA') or (img_pil.mode == 'P' and 'transparency' in img_pil.info):
            # Buat canvas putih baru seukuran gambar asli
            new_img = Image.new("RGB", img_pil.size, (255, 255, 255))
            # Tempel gambar asli (dengan mask transparansinya) ke atas canvas putih
            new_img.paste(img_pil, mask=img_pil.convert('RGBA').split()[3])
            img_pil = new_img
        elif img_pil.mode != 'RGB':
            # Convert mode lain (CMYK, Grayscale dll) ke standard RGB
            img_pil = img_pil.convert('RGB')

        # --- Resize Logic ---
        width, height = img_pil.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            # Hitung rasio untuk resize
            if width > height:
                scaling_factor = MAX_DIMENSION / width
            else:
                scaling_factor = MAX_DIMENSION / height
            
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)
            
            # Gunakan LANCZOS untuk hasil downscaling terbaik
            img_pil = img_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # --- Save to JPEG Buffer ---
        buffer = io.BytesIO()
        # optimize=True membantu mengurangi ukuran sedikit lagi tanpa mengurangi kualitas
        img_pil.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        print(f"   ⚠️ Warning: Gagal memproses gambar (mungkin format aneh), skip. Error: {e}")
        return None

def compress_pdf(input_path, output_path):
    print(f"Processing: {input_path}")
    
    # Buka PDF
    try:
        doc = fitz.open(input_path)
    except Exception as e:
         print(f"❌ Error membuka PDF: {e}")
         return

    optimized_count = 0
    skipped_count = 0
    total_images = 0

    # Kita perlu melacak gambar yang sudah diproses agar tidak memproses gambar yang sama dua kali
    # (Satu gambar bisa dipakai berulang kali di halaman berbeda)
    processed_xrefs = set()

    # Loop semua halaman
    for page_num, page in enumerate(doc):
        print(f"📄 Scanning page {page_num + 1}...")
        
        # Dapatkan daftar semua objek gambar di halaman ini
        image_list = page.get_images(full=True)
        
        if not image_list:
            continue

        for img_info in image_list:
            xref = img_info[0] # ID referensi unik gambar tersebut
            total_images += 1
            
            if xref in processed_xrefs:
                continue # Sudah diproses sebelumnya
            
            processed_xrefs.add(xref)

            print(f"   ➡️ Processing Image XREF {xref}...")

            # Ekstrak gambar asli dari PDF
            try:
                base_image = doc.extract_image(xref)
                original_bytes = base_image["image"]
            except Exception as e:
                 print(f"      ❌ Gagal ekstrak XREF {xref}: {e}")
                 continue

            # Proses (Resize + Kompres)
            new_bytes = resize_and_compress_image(original_bytes)

            if new_bytes:
                # Hanya replace jika ukurannya lebih kecil
                if len(new_bytes) < len(original_bytes):
                    # Update stream gambar di dalam PDF
                    doc.update_stream(xref, new_bytes)
                    optimized_count += 1
                    old_kb = len(original_bytes) / 1024
                    new_kb = len(new_bytes) / 1024
                    print(f"      ✨ Optimized: {old_kb:.1f}KB -> {new_kb:.1f}KB")
                else:
                    print("      Skip: Hasil kompresi lebih besar.")
                    skipped_count += 1
            else:
                skipped_count += 1

    # Simpan PDF final
    # garbage=4: Tingkat pembersihan sampah tertinggi (menghapus objek tak terpakai, duplikat, dll)
    # deflate=True: Mengompres ulang stream non-gambar (seperti teks dan vektor)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    
    print("-" * 30)
    print(f"✅ Selesai!")
    print(f"Total gambar unik ditemukan: {len(processed_xrefs)}")
    print(f"Dioptimalkan: {optimized_count}")
    print(f"Dilewati/Gagal: {skipped_count}")
    
    old_size = os.path.getsize(input_path) / (1024 * 1024)
    new_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Ukuran file: {old_size:.2f} MB -> {new_size:.2f} MB")

if __name__ == "__main__":
    input_pdf = "input.pdf"       # Ganti nama file inputmu
    output_pdf = "output_safe.pdf" 
    
    compress_pdf(input_pdf, output_pdf)