from flask import Flask, render_template, request, redirect, flash, jsonify, session
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import json

def getDatabase():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sekolah_renang_sibahah"
    )

app = Flask(__name__, template_folder='template')
app.secret_key = "secretkey"

@app.route('/')
def landingPage():
    return render_template('regionSatu/index.html')

@app.route('/pendaftaran')
def pendaftaran():
    return render_template('regionSatu/pendaftaran.html')

@app.route('/dashboard/admin')
def admin_dashboard():
    return render_template('regionSatu/admin/dashboard.html')

@app.route('/admin/students')
def admin_students():
    return render_template('regionSatu/admin/students.html')

@app.route('/admin/registrations')
def admin_registrations():
    return render_template('regionSatu/admin/registrations.html')

@app.route('/admin/payments')
def admin_payments():
    return render_template('regionSatu/admin/payments.html')

@app.route('/admin/schedule')
def admin_schedule():
    return render_template('regionSatu/admin/schedule.html')

@app.route('/admin/settings')
def admin_settings():
    return render_template('regionSatu/admin/settings.html')

@app.route('/admin/student-detail')
def admin_student_detail():
    return render_template('regionSatu/admin/student-detail.html')

@app.route('/admin/payment-detail')
def admin_payment_detail():
    return render_template('regionSatu/admin/payment-detail.html')

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

# Route untuk menyimpan data pembayaran ke database
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
        
        # Update data pembayaran di database
        query = """
        UPDATE pendaftaran 
        SET status_pembayaran = 'SUDAH_BAYAR',
            metode_pembayaran = %s,
            tanggal_pembayaran = NOW(),
            nama_pengirim = %s,
            nomor_rekening_pengirim = %s,
            catatan_transfer = %s,
            bukti_transfer = %s
        WHERE id = %s
        """
        
        values = (
            data.get('metode_pembayaran', 'Bank Transfer'),
            data.get('namaPengirim', ''),
            data.get('nomorRekening', ''),
            data.get('catatan', ''),
            bukti_transfer,
            registration_id
        )
        
        print(f"[PAYMENT] Executing query with registration_id: {registration_id}")
        
        cursor.execute(query, values)
        affected_rows = cursor.rowcount
        
        print(f"[PAYMENT] Query executed, affected rows: {affected_rows}")
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"[PAYMENT] SUCCESS: Data saved to database")
        
        # Clear session
        session.pop('registration_data', None)
        session.pop('registration_id', None)
        
        return jsonify({
            'success': True, 
            'message': 'Pembayaran berhasil disimpan ke database!',
            'registration_id': registration_id
        }), 201
        
    except Error as err:
        print(f"[PAYMENT] Database error: {err}")
        return jsonify({'success': False, 'message': f'Database error: {str(err)}'}), 500
    except Exception as e:
        print(f"[PAYMENT] Error: {e}")
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
            data['nama'],
            data.get('usia') or None,
            data['gender'],
            data['ortu'],
            data['wa'],
            data.get('email') or None,
            data['kelas'],
            data['jadwal'],
            data.get('catatan') or None
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
        uang_spp = biaya['uang_spp'] if biaya else 100000
        
        # Query semua siswa
        query = """
        SELECT id, nama, usia, gender, ortu, wa, email, kelas, jadwal, 
               catatan, status_pembayaran, metode_pembayaran, 
               tanggal_daftar, tanggal_pembayaran, keterangan
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
        
        # Total pendapatan (asumsi pembayaran fixed 40000 per siswa)
        cursor.execute("SELECT COUNT(*) as total FROM pendaftaran WHERE status_pembayaran = 'SUDAH_BAYAR'")
        total_bayar = cursor.fetchone()['total'] or 0
        total_pendapatan = total_bayar * 40000
        
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
        
        # Query pembayaran yang sudah diverifikasi - include semua field
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer, 40000 as nominal
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
        
        # Query pembayaran yang belum diverifikasi/pending
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer, 40000 as nominal
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
        
        # Query siswa yang status pembayaran SUDAH_BAYAR
        query = """
        SELECT id, nama, wa, email, usia, gender, ortu, kelas, jadwal, catatan,
               status_pembayaran, metode_pembayaran, tanggal_daftar, tanggal_pembayaran, 
               keterangan, nama_pengirim, nomor_rekening_pengirim, catatan_transfer, 
               bukti_transfer, 40000 as nominal
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
               bukti_transfer, 100000 as nominal
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
                'uang_spp': 100000
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
            'uang_spp': 100000
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


if __name__ == '__main__':
    app.run(debug=True)