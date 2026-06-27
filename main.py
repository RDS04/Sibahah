from flask import Flask, render_template, request, redirect, flash, jsonify, session, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import json
import base64
import traceback
from functools import wraps


# Custom JSON Encoder untuk handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


def getDatabase():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sekolah_renang_sibahah"
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            # Jika API request, return JSON error. Jika HTML request, redirect
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Unauthorized - Admin login required'}), 401
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function


app = Flask(__name__, template_folder='template')
app.secret_key = "secretkey"
app.config['SECRET_KEY'] = 'ganti-dengan-string-acak-yang-panjang-dan-unik'  # WAJIB!
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
app.config['SESSION_COOKIE_SECURE'] = False   # Set True jika pakai HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Set custom JSON encoder untuk handle datetime (untuk Flask 2.0+)
try:
    app.json.encoder_class = DateTimeEncoder  # Flask 2.0+
except:
    app.json_encoder = DateTimeEncoder  # Flask < 2.0


# Panggil saat startup
# ensure_admin_table()

@app.route('/')
def landingPage():
    return render_template('regionSatu/index.html')

@app.route('/pendaftaran')
def pendaftaran():
    return render_template('regionSatu/pendaftaran.html')


@app.route('/dashboard/admin')
@admin_required
def admin_dashboard():
    return render_template(
        'regionSatu/admin/dashboard.html',
        admin_username=session.get('admin_username'),
        admin_role='Super Admin',  # Role bisa diambil dari database jika ada field role
        admin_id=session.get('admin_id')
    )

@app.route('/admin/students')
@admin_required
def admin_students():
    return render_template('regionSatu/admin/students.html')

@app.route('/admin/registrations')
@admin_required
def admin_registrations():
    return render_template('regionSatu/admin/registrations.html')

@app.route('/admin/payments')
@admin_required
def admin_payments():
    return render_template('regionSatu/admin/payments.html')

@app.route('/admin/schedule')
@admin_required
def admin_schedule():
    return render_template('regionSatu/admin/schedule.html')

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('regionSatu/admin/settings.html')

@app.route('/admin/student-detail')
@admin_required
def admin_student_detail():
    return render_template('regionSatu/admin/student-detail.html')

@app.route('/admin/payment-detail')
@admin_required
def admin_payment_detail():
    return render_template('regionSatu/admin/payment-detail.html')

@app.route('/admin/spp-payments')
@admin_required
def admin_spp_payments():
    return render_template('regionSatu/admin/spp-payments.html')

@app.route('/pembayaran')
def pembayaran():
    # Ambil data dari session jika ada
    registration_data = session.get('registration_data', {})
    registration_id = session.get('registration_id', None)
    
    return render_template('regionSatu/pembayaran.html', 
                         registration_data=registration_data,
                         registration_id=registration_id)

@app.route('/riwayat')
def riwayat():
    return render_template('regionSatu/riwayat.html')

 # pip install bcrypt

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Jika sudah login, redirect ke dashboard
    if session.get('admin_logged_in'):
        return redirect('/dashboard/admin')

    error = None
    success = request.args.get('success')

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            error = 'Username dan password harus diisi'
        else:
            conn = getDatabase()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                'SELECT id, password FROM admin_users WHERE username = %s', 
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if not user or user['password'] != password:
                error = 'Username atau password salah'
            else:
                session.clear()  # Bersihkan session lama
                session.permanent = True
                session['admin_logged_in'] = True
                session['admin_username'] = username
                session['admin_id'] = user['id']
                return redirect('/dashboard/admin')

    return render_template('regionSatu/admin/login.html', error=error, success=success)


@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    error = None
    username_value = ''

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        username_value = username

        if not username or not password or not confirm_password:
            error = 'Semua field harus diisi'
        elif password != confirm_password:
            error = 'Password dan konfirmasi password tidak cocok'
        elif len(username) < 3:
            error = 'Username minimal 3 karakter'
        elif len(password) < 4:
            error = 'Password minimal 4 karakter'
        else:
            conn = getDatabase()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT id FROM admin_users WHERE username = %s', (username,))
            if cursor.fetchone():
                error = 'Username sudah digunakan'
                cursor.close()
                conn.close()
            else:
                cursor.execute(
                    'INSERT INTO admin_users (username, password) VALUES (%s, %s)',
                    (username, password)
                )
                conn.commit()
                cursor.close()
                conn.close()
                return redirect(url_for('admin_login', success='Akun admin berhasil dibuat. Silakan login.'))

    return render_template('regionSatu/admin/register.html', error=error, success=None, username=username_value)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_id', None)
    return redirect('/admin/login')


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_id', None)
    return jsonify({'success': True}), 200


# Route untuk menyimpan data pembayaran ke database (SPLIT: Pendaftaran + SPP)
@app.route('/payment', methods=['POST'])
def payment():
    try:
        print(f"[PAYMENT] Received request")
        print(f"[PAYMENT] Session: {dict(session)}")
        print(f"[PAYMENT] Form data: {request.form}")
        print(f"[PAYMENT] Files: {request.files}")
        
        data = request.form
        registration_id = session.get('registration_id')
        
        print(f"[PAYMENT] Registration ID: {registration_id}")
        
        if not registration_id:
            print(f"[PAYMENT] ERROR: Registration ID not found in session")
            return jsonify({'success': False, 'message': 'Session expired. Silakan daftar ulang.'}), 400
        
        # Ambil file bukti transfer
        file = request.files.get('fileUpload')
        
        if not file or not file.filename:
            print(f"[PAYMENT] ERROR: File not uploaded")
            return jsonify({'success': False, 'message': 'Bukti transfer tidak boleh kosong'}), 400
        
        print(f"[PAYMENT] Processing file: {file.filename}")
        
        # Convert file ke base64
        file_data = file.read()
        import base64
        bukti_transfer = base64.b64encode(file_data).decode('utf-8')
        
        print(f"[PAYMENT] File converted to base64, size: {len(bukti_transfer)}")
        
        # Koneksi ke database
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # ===== FETCH BIAYA dari database biaya_sekolah =====
        print(f"[PAYMENT] STEP 0: Fetching biaya from biaya_sekolah table")
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya_result = cursor.fetchone()
        
        if biaya_result:
            biaya_pendaftaran = biaya_result['uang_pendaftaran'] or 40000
            biaya_spp = biaya_result['uang_spp'] or 160000
        else:
            # Fallback ke default jika biaya_sekolah kosong
            biaya_pendaftaran = 40000
            biaya_spp = 160000
        
        print(f"[PAYMENT] Biaya fetched - Pendaftaran: {biaya_pendaftaran}, SPP: {biaya_spp}")
        
        # ===== STEP 1: Update pendaftaran dengan pembayaran PENDAFTARAN =====
        print(f"[PAYMENT] STEP 1: Updating pendaftaran table with registration payment")
        
        query_pendaftaran = """
        UPDATE pendaftaran 
        SET status_pembayaran = 'SUDAH_BAYAR',
            metode_pembayaran = %s,
            tanggal_pembayaran = NOW(),
            nama_pengirim = %s,
            nomor_rekening_pengirim = %s,
            catatan_transfer = %s,
            bukti_transfer = %s,
            total_biaya = %s
        WHERE id = %s
        """
        
        values_pendaftaran = (
            data.get('metode_pembayaran', 'Bank Transfer'),
            data.get('namaPengirim', ''),
            data.get('nomorRekening', ''),
            data.get('catatan', ''),
            bukti_transfer,
            biaya_pendaftaran,  # Only registration fee
            registration_id
        )
        
        cursor.execute(query_pendaftaran, values_pendaftaran)
        affected_rows_1 = cursor.rowcount
        print(f"[PAYMENT] Pendaftaran updated, affected rows: {affected_rows_1}")
        
        # ===== STEP 2: Get siswa_id dari pendaftaran =====
        print(f"[PAYMENT] STEP 2: Fetching siswa_id from pendaftaran")
        cursor.execute("SELECT id FROM pendaftaran WHERE id = %s", (registration_id,))
        result = cursor.fetchone()
        if not result:
            raise Exception(f"Pendaftaran ID {registration_id} not found")
        
        siswa_id = result['id']
        print(f"[PAYMENT] Siswa ID: {siswa_id}")
        
        # ===== STEP 3: Insert SPP payment untuk bulan pertama =====
        print(f"[PAYMENT] STEP 3: Inserting SPP payment (Rp {biaya_spp:,}) to spp_payments table")
        
        today = datetime.now()
        payment_month = today.strftime('%Y-%m')  # Format: 2025-01
        nama_siswa = data.get('namaPengirim', '')  # Gunakan nama pengirim
        
        query_spp = """
        INSERT INTO spp_payments 
        (pendaftaran_id, siswa_id, payment_month, amount, nama_pengirim, nomor_rekening_pengirim, catatan, bukti_transfer, tanggal_pembayaran)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        values_spp = (
            registration_id,
            siswa_id,
            payment_month,
            biaya_spp,
            nama_siswa,
            data.get('nomorRekening', ''),
            data.get('catatan', ''),
            bukti_transfer
        )
        
        cursor.execute(query_spp, values_spp)
        affected_rows_2 = cursor.rowcount
        spp_payment_id = cursor.lastrowid
        print(f"[PAYMENT] SPP payment inserted, affected rows: {affected_rows_2}, SPP ID: {spp_payment_id}")
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"[PAYMENT] SUCCESS: Data split and saved to 2 databases:")
        print(f"  - Pendaftaran: Rp {biaya_pendaftaran:,}")
        print(f"  - SPP: Rp {biaya_spp:,}")
        print(f"  - Total: Rp {biaya_pendaftaran + biaya_spp:,}")
        
        # Clear session
        session.pop('registration_data', None)
        session.pop('registration_id', None)
        
        return jsonify({
            'success': True, 
            'message': 'Pembayaran berhasil disimpan ke database! (Split: Pendaftaran + SPP)',
            'registration_id': registration_id,
            'spp_payment_id': spp_payment_id,
            'breakdown': {
                'biaya_pendaftaran': biaya_pendaftaran,
                'biaya_spp': biaya_spp,
                'total': biaya_pendaftaran + biaya_spp
            }
        }), 201
        
    except Error as err:
        print(f"[PAYMENT] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[PAYMENT] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# Route untuk menyimpan pembayaran SPP (SPP-only)
@app.route('/payment/spp', methods=['POST'])
def payment_spp():
    try:
        print(f"[PAYMENT SPP] Received request")
        print(f"[PAYMENT SPP] Form data: {request.form}")
        print(f"[PAYMENT SPP] Files: {request.files}")

        data = request.form

        # Determine siswa/pendaftaran id: prefer explicit siswa_id, fallback to session registration_id
        siswa_id = data.get('siswa_id') or data.get('siswa') or session.get('registration_id')
        payment_month = data.get('payment_month') or data.get('month')
        amount = data.get('total_pembayaran') or data.get('amount') or 0

        # Validate file
        file = request.files.get('fileUpload')
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'Bukti transfer tidak boleh kosong'}), 400

        file_data = file.read()
        import base64
        bukti_transfer = base64.b64encode(file_data).decode('utf-8')

        # Ensure table exists
        conn = getDatabase()
        cursor = conn.cursor()
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS spp_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pendaftaran_id INT NULL,
            siswa_id VARCHAR(100) NULL,
            payment_month VARCHAR(20) NULL,
            amount DECIMAL(12,2) NULL,
            nama_pengirim VARCHAR(255) NULL,
            nomor_rekening_pengirim VARCHAR(100) NULL,
            catatan TEXT NULL,
            bukti_transfer LONGTEXT NULL,
            tanggal_pembayaran DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        cursor.execute(create_table_sql)

        insert_sql = """
        INSERT INTO spp_payments (
            pendaftaran_id, siswa_id, payment_month, amount,
            nama_pengirim, nomor_rekening_pengirim, catatan, bukti_transfer
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            session.get('registration_id') if session.get('registration_id') else None,
            siswa_id,
            payment_month,
            float(amount) if amount else 0,
            data.get('namaPengirim', ''),
            data.get('nomorRekening', ''),
            data.get('catatan', ''),
            bukti_transfer
        )

        cursor.execute(insert_sql, values)
        conn.commit()

        inserted_id = cursor.lastrowid

        cursor.close()
        conn.close()

        print(f"[PAYMENT SPP] Inserted spp_payments id={inserted_id}")

        return jsonify({'success': True, 'message': 'Pembayaran SPP berhasil disimpan', 'spp_id': inserted_id}), 201

    except Error as err:
        print(f"[PAYMENT SPP] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[PAYMENT SPP] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# Route untuk menyimpan data pendaftaran ke database
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Validasi data
        required_fields = ['nama', 'ortu', 'wa', 'kelas', 'jadwal', 'gender']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'Field {field} tidak boleh kosong'}), 400
        
        # Koneksi ke database
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Cek apakah nomor WA sudah terdaftar
        cursor.execute("SELECT id FROM pendaftaran WHERE wa = %s", (data['wa'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Nomor WhatsApp sudah terdaftar'}), 400
        
        # Insert data ke database
        query = """
        INSERT INTO pendaftaran 
        (nama, usia, gender, ortu, wa, email, kelas, jadwal, catatan, status_pembayaran, tanggal_daftar)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'BELUM_BAYAR', NOW())
        """
        
        values = (
            data['nama'],                  # wajib
            data.get('usia') or None,      # opsional
            data['gender'],                # wajib
            data['ortu'],                  # wajib
            data['wa'],                    # wajib
            data.get('email') or None,     # opsional
            data['kelas'],                 # wajib
            data['jadwal'],                # wajib
            data.get('catatan') or None    # opsional
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        registration_id = cursor.lastrowid
        
        # Simpan data ke session untuk digunakan di halaman pembayaran
        session['registration_data'] = data
        session['registration_id'] = registration_id
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Pendaftaran berhasil disimpan',
            'registration_id': registration_id,
            'data': data
        }), 201
    
        
    except Error as err:
        print(f"Error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ========== API ENDPOINTS UNTUK ADMIN DASHBOARD ==========

# API: GET semua data siswa
@app.route('/api/students', methods=['GET'])
def api_students():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Ambil biaya dari biaya_sekolah
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya = cursor.fetchone()
        uang_pendaftaran = biaya['uang_pendaftaran'] if biaya else 40000
        uang_spp = biaya['uang_spp'] if biaya else 160000
        
        # Query semua siswa
        query = """
        SELECT id, nama, usia, gender, ortu, wa, email, kelas, jadwal, 
               catatan, status_pembayaran, metode_pembayaran, 
               tanggal_daftar, tanggal_pembayaran, keterangan,
               nama_pengirim, nomor_rekening_pengirim, catatan_transfer, bukti_transfer
        FROM pendaftaran
        ORDER BY tanggal_daftar DESC
        """
        
        cursor.execute(query)
        students = cursor.fetchall()
        
        # Tambahkan biaya ke setiap siswa
        for student in students:
            if student['tanggal_daftar']:
                student['tanggal_daftar'] = student['tanggal_daftar'].strftime('%d-%m-%Y')
            if student['tanggal_pembayaran']:
                student['tanggal_pembayaran'] = student['tanggal_pembayaran'].strftime('%d-%m-%Y')
            student['uang_pendaftaran'] = uang_pendaftaran
            student['uang_spp'] = uang_spp
            # Konversi bukti_transfer dari bytes ke string jika ada
            if student.get('bukti_transfer'):
                if isinstance(student['bukti_transfer'], bytes):
                    student['bukti_transfer'] = student['bukti_transfer'].decode('utf-8')
            else:
                student['bukti_transfer'] = None
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': students,
            'total': len(students)
        }), 200
        
    except Error as err:
        print(f"[API STUDENTS] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API STUDENTS] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: GET statistik dashboard
@app.route('/api/stats', methods=['GET'])
def api_stats():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Total siswa aktif (yang sudah bayar)
        cursor.execute("SELECT COUNT(*) as total FROM pendaftaran WHERE status_pembayaran = 'SUDAH_BAYAR'")
        total_aktif = cursor.fetchone()['total'] or 0
        
        # Total registrasi menunggu
        cursor.execute("SELECT COUNT(*) as total FROM pendaftaran WHERE status_pembayaran = 'BELUM_BAYAR'")
        total_pending = cursor.fetchone()['total'] or 0
        
        # Total pendapatan (ambil dari database)
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya = cursor.fetchone()
        uang_pendaftaran = biaya['uang_pendaftaran'] if biaya else 40000
        uang_spp = biaya['uang_spp'] if biaya else 160000
        total_per_siswa = uang_pendaftaran + uang_spp
        
        cursor.execute("SELECT COUNT(*) as total FROM pendaftaran WHERE status_pembayaran = 'SUDAH_BAYAR'")
        total_bayar = cursor.fetchone()['total'] or 0
        total_pendapatan = total_bayar * total_per_siswa
        
        # Total revenue SPP dari table spp_payments
        total_spp_revenue = 0
        try:
            cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM spp_payments")
            spp_result = cursor.fetchone()
            if spp_result:
                total = spp_result.get('total')
                if total is not None:
                    total_spp_revenue = int(float(total)) if total else 0
            print(f"[API STATS] SPP Revenue Query Success: {spp_result}, Total: {total_spp_revenue}")
        except Exception as spp_err:
            print(f"[API STATS] Error querying spp_payments: {spp_err}")
            import traceback
            traceback.print_exc()
        
        # Breakdown per kelas
        cursor.execute("SELECT kelas, COUNT(*) as jumlah FROM pendaftaran GROUP BY kelas")
        kelas_breakdown = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total_siswa_aktif': total_aktif,
            'total_pendaftaran': total_pending,
            'total_pendapatan': total_pendapatan,
            'total_menunggu_bayar': total_pending,
            'total_spp_revenue': total_spp_revenue,
            'breakdown_kelas': kelas_breakdown
        }), 200
        
    except Error as err:
        print(f"[API STATS] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API STATS] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: GET registrasi yang belum dibayar (pending)
@app.route('/api/registrations', methods=['GET'])
def api_registrations():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Query registrasi menunggu pembayaran
        query = """
        SELECT id, nama, ortu, wa, email, kelas, jadwal, gender, usia,
               status_pembayaran, tanggal_daftar, metode_pembayaran
        FROM pendaftaran
        WHERE status_pembayaran = 'BELUM_BAYAR'
        ORDER BY tanggal_daftar DESC
        """
        
        cursor.execute(query)
        registrations = cursor.fetchall()
        
        # Format tanggal
        for reg in registrations:
            if reg['tanggal_daftar']:
                reg['tanggal_daftar'] = reg['tanggal_daftar'].strftime('%d-%m-%Y %H:%M')
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': registrations,
            'total': len(registrations)
        }), 200
        
    except Error as err:
        print(f"[API REGISTRATIONS] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API REGISTRATIONS] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: GET riwayat pembayaran
@app.route('/api/payments', methods=['GET'])
def api_payments():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Ambil biaya dari database
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya = cursor.fetchone()
        uang_pendaftaran = biaya['uang_pendaftaran'] if biaya else 40000
        uang_spp = biaya['uang_spp'] if biaya else 160000
        total_nominal = uang_pendaftaran + uang_spp
        
        # Query pembayaran yang sudah diverifikasi - include semua field
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer
        FROM pendaftaran
        WHERE status_pembayaran = 'SUDAH_BAYAR'
        ORDER BY tanggal_pembayaran DESC
        """
        
        cursor.execute(query)
        payments = cursor.fetchall()
        
        # Format tanggal dan convert bukti_transfer bytes ke base64
        for payment in payments:
            if payment['tanggal_pembayaran']:
                payment['tanggal_pembayaran'] = payment['tanggal_pembayaran'].strftime('%d-%m-%Y')
            if payment['tanggal_daftar']:
                payment['tanggal_daftar'] = payment['tanggal_daftar'].strftime('%d-%m-%Y')
            # Convert bukti_transfer bytes ke base64 string (atau None jika kosong)
            if payment['bukti_transfer']:
                if isinstance(payment['bukti_transfer'], bytes):
                    payment['bukti_transfer'] = payment['bukti_transfer'].decode('utf-8')
            else:
                payment['bukti_transfer'] = None
            # Tambahkan nominal pembayaran
            payment['uang_pendaftaran'] = uang_pendaftaran
            payment['uang_spp'] = uang_spp
            payment['nominal'] = total_nominal
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': payments,
            'total': len(payments)
        }), 200
        
    except Error as err:
        print(f"[API PAYMENTS] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API PAYMENTS] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: GET pembayaran pending
@app.route('/api/payments/pending', methods=['GET'])
def api_payments_pending():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Ambil biaya dari database
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya = cursor.fetchone()
        uang_pendaftaran = biaya['uang_pendaftaran'] if biaya else 40000
        uang_spp = biaya['uang_spp'] if biaya else 160000
        total_nominal = uang_pendaftaran + uang_spp
        
        # Query pembayaran yang belum diverifikasi/pending
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer
        FROM pendaftaran
        WHERE status_pembayaran != 'SUDAH_BAYAR'
        ORDER BY tanggal_daftar DESC
        """
        
        cursor.execute(query)
        payments = cursor.fetchall()
        
        # Format tanggal dan convert bukti_transfer
        for payment in payments:
            if payment['tanggal_pembayaran']:
                payment['tanggal_pembayaran'] = payment['tanggal_pembayaran'].strftime('%d-%m-%Y')
            if payment['tanggal_daftar']:
                payment['tanggal_daftar'] = payment['tanggal_daftar'].strftime('%d-%m-%Y')
            if payment['bukti_transfer']:
                if isinstance(payment['bukti_transfer'], bytes):
                    payment['bukti_transfer'] = payment['bukti_transfer'].decode('utf-8')
            else:
                payment['bukti_transfer'] = None
            # Tambahkan nominal pembayaran
            payment['uang_pendaftaran'] = uang_pendaftaran
            payment['uang_spp'] = uang_spp
            payment['nominal'] = total_nominal
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': payments,
            'total': len(payments)
        }), 200
        
    except Error as err:
        print(f"[API PAYMENTS PENDING] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API PAYMENTS PENDING] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: Pembayaran Pendaftaran (Students who paid registration)
@app.route('/api/payments/registration', methods=['GET'])
def api_payments_registration():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Ambil biaya dari database
        cursor.execute("SELECT uang_pendaftaran, uang_spp FROM biaya_sekolah WHERE id = 1")
        biaya = cursor.fetchone()
        uang_pendaftaran = biaya['uang_pendaftaran'] if biaya else 40000
        uang_spp = biaya['uang_spp'] if biaya else 160000
        total_nominal = uang_pendaftaran + uang_spp
        
        # Query siswa yang status pembayaran SUDAH_BAYAR
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer
        FROM pendaftaran
        WHERE status_pembayaran = 'SUDAH_BAYAR'
        ORDER BY tanggal_pembayaran DESC
        """
        
        cursor.execute(query)
        payments = cursor.fetchall()
        
        # Format tanggal dan convert bukti_transfer
        for payment in payments:
            if payment['tanggal_pembayaran']:
                payment['tanggal_pembayaran'] = payment['tanggal_pembayaran'].strftime('%d-%m-%Y')
            if payment['tanggal_daftar']:
                payment['tanggal_daftar'] = payment['tanggal_daftar'].strftime('%d-%m-%Y')
            if payment['bukti_transfer']:
                if isinstance(payment['bukti_transfer'], bytes):
                    payment['bukti_transfer'] = payment['bukti_transfer'].decode('utf-8')
            else:
                payment['bukti_transfer'] = None
            # Tambahkan nominal pembayaran
            payment['uang_pendaftaran'] = uang_pendaftaran
            payment['uang_spp'] = uang_spp
            payment['nominal'] = total_nominal
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': payments,
            'total': len(payments)
        }), 200
        
    except Error as err:
        print(f"[API PAYMENTS REGISTRATION] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API PAYMENTS REGISTRATION] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: Pembayaran SPP (Students who paid SPP)
@app.route('/api/payments/spp', methods=['GET'])
def api_payments_spp():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Query siswa yang membayar SPP - assume they paid SPP jika status pembayaran = SUDAH_BAYAR
        # dan tanggal pembayaran lebih dari 1 bulan setelah tanggal daftar
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer, 160000 as nominal
        FROM pendaftaran
        WHERE status_pembayaran = 'SUDAH_BAYAR'
        ORDER BY tanggal_pembayaran DESC
        """
        
        cursor.execute(query)
        payments = cursor.fetchall()
        
        # Format tanggal dan convert bukti_transfer
        for payment in payments:
            if payment['tanggal_pembayaran']:
                payment['tanggal_pembayaran'] = payment['tanggal_pembayaran'].strftime('%d-%m-%Y')
            if payment['tanggal_daftar']:
                payment['tanggal_daftar'] = payment['tanggal_daftar'].strftime('%d-%m-%Y')
            if payment['bukti_transfer']:
                if isinstance(payment['bukti_transfer'], bytes):
                    payment['bukti_transfer'] = payment['bukti_transfer'].decode('utf-8')
            else:
                payment['bukti_transfer'] = None
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': payments,
            'total': len(payments)
        }), 200
        
    except Error as err:
        print(f"[API PAYMENTS SPP] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API PAYMENTS SPP] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: GET daftar spp_payments (yang tersimpan melalui /payment/spp)
@app.route('/api/spp_payments', methods=['GET'])
def api_spp_payments():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, pendaftaran_id, siswa_id, payment_month, amount,
               nama_pengirim, nomor_rekening_pengirim, catatan, bukti_transfer, tanggal_pembayaran
        FROM spp_payments
        ORDER BY tanggal_pembayaran DESC
        LIMIT 200
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        # Format tanggal
        for r in rows:
            if r.get('tanggal_pembayaran'):
                try:
                    r['tanggal_pembayaran'] = r['tanggal_pembayaran'].strftime('%d-%m-%Y %H:%M')
                except Exception:
                    pass
            # bukti_transfer dibiarkan sebagai base64 string (atau NULL)

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'data': rows, 'total': len(rows)}), 200

    except Error as err:
        print(f"[API SPP_PAYMENTS] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API SPP_PAYMENTS] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ========== API ENDPOINTS UNTUK MANAJEMEN BIAYA ==========

# API: GET biaya sekolah (uang pendaftaran & SPP)
@app.route('/api/biaya', methods=['GET'])
def api_biaya():
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Ambil data biaya dari tabel biaya_sekolah
        cursor.execute("""
            SELECT uang_pendaftaran, uang_spp, keterangan 
            FROM biaya_sekolah 
            WHERE id = 1
        """)
        biaya = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not biaya:
            return jsonify({
                'success': True,
                'uang_pendaftaran': 40000,
                'uang_spp': 160000
            }), 200
        
        return jsonify({
            'success': True,
            'uang_pendaftaran': biaya['uang_pendaftaran'],
            'uang_spp': biaya['uang_spp'],
            'keterangan': biaya['keterangan']
        }), 200
        
    except Error as err:
        print(f"[API BIAYA] Database error: {err}")
        return jsonify({
            'success': True,
            'uang_pendaftaran': 40000,
            'uang_spp': 160000
        }), 200

# API: UPDATE biaya sekolah
@app.route('/api/biaya', methods=['PUT'])
def api_biaya_update():
    try:
        data = request.json
        
        uang_pendaftaran = data.get('uang_pendaftaran')
        uang_spp = data.get('uang_spp')
        keterangan = data.get('keterangan')
        
        if uang_pendaftaran is None or uang_spp is None:
            return jsonify({'success': False, 'message': 'Biaya pendaftaran dan SPP harus diisi'}), 400
        
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Update biaya
        cursor.execute("""
            UPDATE biaya_sekolah 
            SET uang_pendaftaran = %s, uang_spp = %s, keterangan = %s
            WHERE id = 1
        """, (uang_pendaftaran, uang_spp, keterangan))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Biaya berhasil diperbarui'
        }), 200
        
    except Error as err:
        print(f"[API BIAYA UPDATE] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[API BIAYA UPDATE] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API: CEK Status Pembayaran SPP Siswa per Bulan
@app.route('/api/check-payment/<student_id>/<month>', methods=['GET'])
def check_student_payment_status(student_id, month):
    """
    Check apakah siswa sudah membayar SPP untuk bulan tertentu (1-12)
    """
    try:
        student_id = int(student_id)
        month = int(month)
        
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        
        # Cek apakah ada record pembayaran untuk bulan ini
        cursor.execute(
            "SELECT id, tanggal_pembayaran, amount FROM spp_payments WHERE siswa_id = %s AND payment_month = %s LIMIT 1",
            (student_id, month)
        )
        payment_record = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        is_paid = payment_record is not None
        
        return jsonify({
            'success': True,
            'is_paid': is_paid,
            'current_month': datetime.now().month,
            'check_month': month,
            'siswa_id': student_id,
            'payment_date': payment_record['tanggal_pembayaran'] if is_paid else None,
            'amount': payment_record['amount'] if is_paid else None
        }), 200
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid student_id or month', 'is_paid': False}), 400
    except Error as err:
        print(f"[CHECK PAYMENT] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}', 'is_paid': False}), 500
    except Exception as e:
        print(f"[CHECK PAYMENT] Error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}', 'is_paid': False}), 500


# TEST: Simple test endpoint
@app.route('/api/test-hello', methods=['GET'])
def test_hello():
    return jsonify({'message': 'Hello from Test'}), 200


# ===== JADWAL LATIHAN ENDPOINTS =====

@app.route('/api/jadwal', methods=['GET'])
def get_jadwal():
    """GET semua jadwal latihan"""
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM jadwal_latihan 
            WHERE is_active = TRUE 
            ORDER BY FIELD(hari, 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'), 
                     jam_mulai ASC
        """)
        jadwal_list = cursor.fetchall()
        cursor.close()
        conn.close()
        print(f'[API JADWAL] SUCCESS: {len(jadwal_list)} schedules loaded')
        return jsonify({'success': True, 'data': jadwal_list}), 200
    except Error as err:
        print(f'[API JADWAL] Database error: {err}')
        return jsonify({'success': False, 'message': str(err)}), 500
    except Exception as e:
        print(f'[API JADWAL] Unexpected error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/jadwal/<int:jenis_id>', methods=['GET'])
def get_jadwal_by_jenis(jenis_id):
    """GET jadwal berdasarkan jenis (1=Putra, 2=Putri)"""
    jenis_map = {1: 'Putra', 2: 'Putri'}
    jenis = jenis_map.get(jenis_id, 'Putra')
    
    try:
        conn = getDatabase()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM jadwal_latihan 
            WHERE jenis = %s AND is_active = TRUE
            ORDER BY FIELD(hari, 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'), 
                     jam_mulai ASC
        """, (jenis,))
        jadwal_list = cursor.fetchall()
        cursor.close()
        conn.close()
        print(f'[API JADWAL BY JENIS] Jenis={jenis}, Count={len(jadwal_list)}')
        return jsonify({'success': True, 'data': jadwal_list}), 200
    except Error as err:
        print(f'[API JADWAL BY JENIS] Database error: {err}')
        return jsonify({'success': False, 'message': str(err)}), 500
    except Exception as e:
        print(f'[API JADWAL BY JENIS] Unexpected error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/jadwal', methods=['POST'])
@admin_required
def create_jadwal():
    """POST jadwal baru (Admin only)"""
    try:
        data = request.get_json()
        hari = data.get('hari')
        jam_mulai = data.get('jam_mulai')
        jam_selesai = data.get('jam_selesai')
        kelas = data.get('kelas')
        jenis = data.get('jenis')
        instruktur = data.get('instruktur', '')
        kapasitas = data.get('kapasitas', 15)
        
        if not all([hari, jam_mulai, jam_selesai, kelas, jenis]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        conn = getDatabase()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jadwal_latihan 
            (hari, jam_mulai, jam_selesai, kelas, jenis, instruktur, kapasitas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (hari, jam_mulai, jam_selesai, kelas, jenis, instruktur, kapasitas))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'id': new_id, 'message': 'Jadwal berhasil ditambahkan'}), 201
    except Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500


@app.route('/api/jadwal/<int:jadwal_id>', methods=['PUT'])
@admin_required
def update_jadwal(jadwal_id):
    """PUT update jadwal (Admin only)"""
    try:
        data = request.get_json()
        conn = getDatabase()
        cursor = conn.cursor()
        
        # Build update query dynamically
        fields = []
        values = []
        allowed_fields = ['hari', 'jam_mulai', 'jam_selesai', 'kelas', 'jenis', 'instruktur', 'kapasitas', 'peserta', 'is_active']
        
        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not fields:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'No fields to update'}), 400
        
        values.append(jadwal_id)
        query = f"UPDATE jadwal_latihan SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Jadwal berhasil diupdate'}), 200
    except Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500


@app.route('/api/jadwal/<int:jadwal_id>', methods=['DELETE'])
@admin_required
def delete_jadwal(jadwal_id):
    """DELETE jadwal (soft delete - set is_active=FALSE)"""
    try:
        conn = getDatabase()
        cursor = conn.cursor()
        cursor.execute("UPDATE jadwal_latihan SET is_active = FALSE WHERE id = %s", (jadwal_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Jadwal berhasil dihapus'}), 200
    except Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)