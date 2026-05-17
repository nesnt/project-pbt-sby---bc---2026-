import requests
from PIL import Image
from io import BytesIO

def ambil_data_dari_server():
    url_api = "http://192.168.1.15:8000/produk" # IP Laptop Server kamu
    
    try:
        response = requests.get(url_api)
        if response.status_code == 200:
            data_produk = response.json()
            
            for produk in data_produk:
                print(f"Nama: {produk['nama_barang']}")
                print(f"Link Gambar: {produk['url_gambar']}")
                
                # Contoh cara 'get' atau mengambil gambar untuk ditampilkan
                respon_gambar = requests.get(produk['url_gambar'])
                img = Image.open(BytesIO(respon_gambar.content))
                img.show() # Ini akan membuka viewer foto bawaan OS
                
        else:
            print("Gagal mengambil data.")
    except Exception as e:
        print(f"Terjadi kesalahan koneksi: {e}")

if __name__ == "__main__":
    ambil_data_dari_server()