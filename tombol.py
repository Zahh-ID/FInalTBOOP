import tkinter as tk
from math import sin, cos, pi
def tbl(canvas, x, y, lebar, tinggi, radius_awal, radius_akhir, 
        sudut_awal_busur1, sudut_akhir_busur1, 
        sudut_awal_busur2, sudut_akhir_busur2, 
        warna, teks, perintah):
    """
    Membuat tombol dengan bentuk kustom menggunakan poligon dan busur yang diisi.
    Parameter sudut_awal/akhir_busur1/2 menentukan 'extent' jika tbl Anda menghitungnya.
    Jika tbl Anda membuat sudut standar, nilai-nilai ini mungkin tidak terlalu berpengaruh.
    Versi ini menggambar 4 sudut membulat standar.
    """
    
    path_id = canvas.create_polygon(
        x + radius_awal, y, 
        x + lebar - radius_akhir, y, 
        x + lebar - radius_akhir, y, 
        x + lebar, y + radius_akhir, 
        x + lebar, y + tinggi - radius_akhir, 
        x + lebar - radius_akhir, y + tinggi, 
        x + radius_awal, y + tinggi, 
        x, y + tinggi - radius_awal, 
        x, y + radius_awal, 
        x + radius_awal, y, 
        fill=warna,
        outline=warna,
        smooth=False 
    )

    # Sudut Kiri Atas
    canvas.create_arc(
        x, y, 
        x + 2 * radius_awal, y + 2 * radius_awal,
        start=90, extent=90, 
        style=tk.PIESLICE, fill=warna, outline=warna
    )
    # Sudut Kanan Atas
    canvas.create_arc(
        x + lebar - 2 * radius_akhir, y,
        x + lebar, y + 2 * radius_akhir,
        start=0, extent=90, 
        style=tk.PIESLICE, fill=warna, outline=warna
    )
    # Sudut Kiri Bawah
    canvas.create_arc(
        x, y + tinggi - 2 * radius_awal,
        x + 2 * radius_awal, y + tinggi,
        start=180, extent=90, 
        style=tk.PIESLICE, fill=warna, outline=warna
    )
    # Sudut Kanan Bawah
    canvas.create_arc(
        x + lebar - 2 * radius_akhir, y + tinggi - 2 * radius_akhir,
        x + lebar, y + tinggi,
        start=270, extent=90, 
        style=tk.PIESLICE, fill=warna, outline=warna
    )
    
    teks_id = canvas.create_text(x + lebar / 2, y + tinggi / 2, text=teks, fill="white", font=("Arial", 12, "bold"))

    button_tag = f"button_custom_{path_id}" 
    canvas.addtag_withtag(button_tag, path_id)

    def klik_tombol(event):
        perintah()

    canvas.tag_bind(path_id, "<Button-1>", klik_tombol)
    canvas.tag_bind(teks_id, "<Button-1>", klik_tombol)
    
    return path_id, teks_id