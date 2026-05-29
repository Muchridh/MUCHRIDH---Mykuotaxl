# app.py - Versi REST API Supabase
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Konfigurasi Supabase
SUPABASE_URL = 'https://uzejdqnlkfbtlgpxfcuk.supabase.co'

# Gunakan ANON KEY (bukan service_role)
SUPABASE_ANON_KEY = 'sb_publishable_-P6EFatraTuSN-_HDKQGjA_TkiOFgSL'

HEADERS = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json'
}

def supabase_get(endpoint, params=None):
    """Helper function untuk GET request ke Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        print(f"📡 GET {url} - Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

@app.route('/api/kuota/<nomor>', methods=['GET'])  # PERBAIKI: tambahkan <nomor>
def get_latest_kuota(nomor):
    """Get latest kuota data"""
    try:
        # 1. Ambil data terbaru dari kuota_checks
        params = {
            'nomor_pelanggan': f'eq.{nomor}',
            'order': 'created_at.desc',
            'limit': '1'
        }
        
        checks = supabase_get('kuota_checks', params)
        
        if not checks or len(checks) == 0:
            return jsonify({
                'error': 'Data tidak ditemukan',
                'message': f'Belum ada data untuk nomor {nomor}'
            }), 404
        
        check = checks[0]
        check_id = check['id']
        
        # 2. Ambil paket untuk check_id ini
        paket_params = {
            'check_id': f'eq.{check_id}'
        }
        pakets = supabase_get('paket_details', paket_params)
        
        paket_list = []
        if pakets:
            for paket in pakets:
                # 3. Ambil benefit untuk setiap paket
                benefit_params = {
                    'paket_id': f'eq.{paket["id"]}'
                }
                benefits = supabase_get('benefit_details', benefit_params)
                
                paket_list.append({
                    'nama_paket': paket.get('nama_paket', ''),
                    'expired': paket.get('expired', ''),
                    'benefits': benefits or []
                })
        
        response = {
            'nomor_pelanggan': check.get('nomor_pelanggan', ''),
            'timestamp': check.get('created_at', ''),
            'paket': paket_list
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<nomor>', methods=['GET'])  # PERBAIKI: tambahkan <nomor>
def get_history(nomor):
    """Get history kuota checks"""
    try:
        days = request.args.get('days', 7, type=int)
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        params = {
            'nomor_pelanggan': f'eq.{nomor}',
            'created_at': f'gte.{since_date}',
            'order': 'created_at.desc',
            'limit': '10',
            'select': 'id,nomor_pelanggan,created_at'
        }
        
        history = supabase_get('kuota_checks', params)
        
        return jsonify(history or [])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_total_sisa_quota(check_id):
    """Helper to get total sisa quota in GB for a specific check_id"""
    pakets = supabase_get('paket_details', {'check_id': f'eq.{check_id}'})
    if not pakets: return 0
    total_gb = 0
    for p in pakets:
        benefits = supabase_get('benefit_details', {'paket_id': f'eq.{p["id"]}'})
        if benefits:
            for b in benefits:
                sq = b.get('sisa_quota', '')
                if 'GB' in sq.upper():
                    try:
                        val = float(sq.upper().replace('GB', '').replace(',', '.').strip())
                        total_gb += val
                    except: pass
                elif 'MB' in sq.upper():
                    try:
                        val = float(sq.upper().replace('MB', '').replace(',', '.').strip())
                        total_gb += val / 1024
                    except: pass
    return total_gb

@app.route('/api/usage/<nomor>', methods=['GET'])
def get_usage_summary(nomor):
    """Get usage summary for hari (daily), minggu (weekly), bulan (monthly)"""
    try:
        filter_type = request.args.get('filter', 'hari') # hari, minggu, bulan
        
        # 1. Get latest check
        latest_checks = supabase_get('kuota_checks', {
            'nomor_pelanggan': f'eq.{nomor}',
            'order': 'created_at.desc',
            'limit': '1'
        })
        
        if not latest_checks:
            return jsonify({'usage_gb': 0, 'message': 'No data'})
            
        latest_check = latest_checks[0]
        latest_sisa = get_total_sisa_quota(latest_check['id'])
        
        # 2. Determine past date based on filter
        now = datetime.now()
        if filter_type == 'hari':
            # Compare with yesterday 23:59 (basically the last record from yesterday)
            past_date = (now - timedelta(days=1)).strftime('%Y-%m-%d 23:59:59')
        elif filter_type == 'minggu':
            past_date = (now - timedelta(days=7)).isoformat()
        elif filter_type == 'bulan':
            past_date = (now - timedelta(days=30)).isoformat()
        else:
            past_date = (now - timedelta(days=1)).isoformat()
            
        # 3. Get the check closest to the past_date (before or at past_date)
        past_checks = supabase_get('kuota_checks', {
            'nomor_pelanggan': f'eq.{nomor}',
            'created_at': f'lte.{past_date}',
            'order': 'created_at.desc',
            'limit': '1'
        })
        
        usage_gb = 0
        if past_checks and len(past_checks) > 0:
            past_check = past_checks[0]
            past_sisa = get_total_sisa_quota(past_check['id'])
            # Usage is past remaining - current remaining
            usage_gb = max(0, past_sisa - latest_sisa)
            
        return jsonify({
            'filter': filter_type,
            'usage_gb': round(usage_gb, 2),
            'latest_sisa_gb': round(latest_sisa, 2),
            'past_date': past_date
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Test koneksi ke Supabase
    test = supabase_get('kuota_checks', {'limit': '1'})
    
    return jsonify({
        'status': 'OK',
        'database': 'connected' if test is not None else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Test endpoint untuk cek semua tabel"""
    result = {}
    
    # Test kuota_checks
    checks = supabase_get('kuota_checks', {'limit': '1'})
    result['kuota_checks'] = 'OK' if checks is not None else 'ERROR'
    
    # Test paket_details
    pakets = supabase_get('paket_details', {'limit': '1'})
    result['paket_details'] = 'OK' if pakets is not None else 'ERROR'
    
    # Test benefit_details
    benefits = supabase_get('benefit_details', {'limit': '1'})
    result['benefit_details'] = 'OK' if benefits is not None else 'ERROR'
    
    return jsonify({
        'tables': result,
        'message': 'Semua tabel OK!' if all(v == 'OK' for v in result.values()) else 'Ada tabel yang bermasalah'
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 MyKuota API Server (REST Mode)")
    print("="*60)
    print(f"📡 URL: http://localhost:5000")
    print(f"💾 Supabase: {SUPABASE_URL}")
    print("\n📋 Endpoints:")
    print("   GET /api/kuota/<nomor>     - Cek kuota terbaru")
    print("   GET /api/history/<nomor>   - Riwayat pengecekan")
    print("   GET /api/health            - Status server")
    print("   GET /api/test              - Test koneksi database")
    print("\n💡 Contoh penggunaan:")
    print("   http://localhost:5000/api/kuota/081809911100")
    print("   http://localhost:5000/api/health")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)