# 📊 Automasi Monitor Kuota SiDompul (XL/Axis) 🚀

![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=flat-square&logo=github-actions)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=flat-square&logo=supabase)
![Serverless](https://img.shields.io/badge/Architecture-Serverless-FF9900?style=flat-square)

Sistem automasi *serverless* terintegrasi untuk memantau sisa kuota internet XL/Axis secara *real-time*. Proyek ini menggunakan **Telegram Userbot (Telethon)** yang dijalankan otomatis oleh **GitHub Actions**, menyimpan riwayat data terstruktur di **Supabase**, dan menampilkannya melalui **Dashboard HTML Serverless** yang di-*hosting* di GitHub Pages.

---

## ✨ Fitur Utama

- ☁️ **100% Serverless:** Tidak memerlukan server VPS, hosting lokal, maupun *backend* Python (Flask/Django) yang menyala 24 jam.
- 🤖 **Automasi Userbot:** Mengekstrak data langsung dari bot resmi `@Sidompul_XL_AXIS_bot` tanpa perlu interaksi manual.
- 🕒 **Penjadwalan Pintar (Cron):** Berjalan otomatis sesuai jadwal yang ditentukan (contoh: setiap 2/8 jam) menghindari jam *maintenance* server provider.
- 🗄️ **Database Relasional:** Data kuota, paket, dan benefit tersimpan rapi menggunakan arsitektur relasional 3 tabel di Supabase.
- 📈 **Dashboard Interaktif:** UI elegan yang berkomunikasi langsung dengan REST API Supabase (*Direct Frontend-to-Database*).

---

## 🛠️ Prasyarat (Requirements)

Sebelum memulai *deployment*, pastikan Anda telah memiliki:
1. **API ID & API Hash Telegram:** Dapatkan dari [my.telegram.org](https://my.telegram.org).
2. **Akun Supabase:** Buat *project* baru di [supabase.com](https://supabase.com).
3. **Akun GitHub:** Untuk menyimpan kode dan menjalankan automasi.

---

## ⚙️ Cara Instalasi & Pengaturan (Setup Guide)

Ikuti langkah-langkah di bawah ini agar sistem dapat berjalan normal tanpa hambatan.

### Langkah 1: Persiapan Database Supabase
1. Buat *project* baru di Supabase.
2. Buka menu **SQL Editor**, lalu jalankan *query* berikut untuk membuat 3 tabel yang dibutuhkan:

```sql
-- Tabel Log Utama
CREATE TABLE kuota_checks (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone DEFAULT now(),
  nomor_pelanggan text,
  raw_data jsonb
);

-- Tabel Detail Paket
CREATE TABLE paket_details (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  check_id uuid REFERENCES kuota_checks(id) ON DELETE CASCADE,
  nama_paket text,
  expired text
);

-- Tabel Detail Benefit (Kuota Utama, Telp, SMS, dll)
CREATE TABLE benefit_details (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  paket_id uuid REFERENCES paket_details(id) ON DELETE CASCADE,
  nama_benefit text,
  quota text,
  sisa_quota text
);
