import pikepdf
import io
from PIL import Image
import sys

def compress_pdf_robust(input_pdf, output_pdf, quality=60):
    try:
        print(f"Opening: {input_pdf}")
        with pikepdf.open(input_pdf) as pdf:
            count = 0
            for page_idx, page in enumerate(pdf.pages):
                if "/Resources" not in page or "/XObject" not in page.Resources:
                    continue
                
                xobjects = page.Resources.XObject
                for name, obj in xobjects.items():
                    if obj.get("/Subtype") == "/Image":
                        print(f"Compressing image {name} on page {page_idx + 1}...")
                        try:
                            # Extract
                            pdfimg = pikepdf.PdfImage(obj)
                            pil_img = pdfimg.as_pil_image()
                            
                            # Process transparency (flatten to white background)
                            if pil_img.mode in ('RGBA', 'P', 'LA'):
                                background = Image.new('RGB', pil_img.size, (255, 255, 255))
                                if pil_img.mode == 'P':
                                    pil_img = pil_img.convert('RGBA')
                                
                                # Use alpha channel as mask if present
                                if 'A' in pil_img.mode or pil_img.mode == 'RGBA':
                                    background.paste(pil_img, mask=pil_img.split()[3])
                                else:
                                    background.paste(pil_img)
                                pil_img = background
                            else:
                                pil_img = pil_img.convert('RGB')
                                
                            # Resize if too large
                            if pil_img.width > 1200:
                                ratio = 1200 / pil_img.width
                                pil_img = pil_img.resize((1200, int(pil_img.height * ratio)), Image.LANCZOS)
                                
                            # Save to buffer
                            img_io = io.BytesIO()
                            pil_img.save(img_io, format='JPEG', quality=quality)
                            
                            # Create new stream for replacement
                            new_img = pikepdf.Stream(pdf, img_io.getvalue(),
                                                     Type=pikepdf.Name.XObject,
                                                     Subtype=pikepdf.Name.Image,
                                                     Width=pil_img.width,
                                                     Height=pil_img.height,
                                                     ColorSpace=pikepdf.Name.DeviceRGB,
                                                     BitsPerComponent=8,
                                                     Filter=pikepdf.Name.DCTDecode)
                            
                            xobjects[name] = new_img
                            count += 1
                            
                        except Exception as e:
                            print(f"Error processing {name}: {e}")
                            
            print(f"Saving to {output_pdf} (processed {count} images)...")
            pdf.save(output_pdf, linearize=True)
            print("Success!")
            
    except Exception as e:
        print(f"Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if input file exists
    import os
    if not os.path.exists("input.pdf"):
        print("Error: input.pdf not found in current directory.")
        sys.exit(1)
        
    compress_pdf_robust("input.pdf", "output_pikepdf.pdf")
