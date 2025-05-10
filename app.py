from flask import Flask, render_template, request, redirect, url_for
from models import db, ProductionCost, Revenue, Tourism, Account, Transaction, JournalEntry
from datetime import datetime
from sqlalchemy.orm import joinedload


app = Flask(__name__)
app.secret_key = 'rahasia-sangat-kuat'
app.jinja_env.filters['attribute'] = getattr
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.jinja_env.globals['getattr'] = getattr
db.init_app(app)
with app.app_context():
    db.create_all()
    
    if not Account.query.first():
        # Hitung total biaya produksi
        total_biaya = sum(
            i.land_area + 
            i.seed_cost + 
            i.fertilizer_cost + 
            i.medicine_cost + 
            i.equipment_cost + 
            i.labor_cost + 
            i.electricity_cost + 
            i.water_cost 
            for i in ProductionCost.query.all()
        )
        
        # Hitung total pendapatan penjualan
        total_pendapatan = sum(
            i.price_per_kg * i.strawberry_amount 
            for i in Revenue.query.all()
        )
        
        # Hitung total pendapatan wisata
        total_wisata = sum(
            i.ticket_price * i.visitor_count 
            for i in Tourism.query.all()
        )
        
        # Hitung saldo awal
        starting = (total_pendapatan - total_biaya) + total_wisata
        
        # Buat akun pertama
        db.session.add(Account(current_balance=starting))
        db.session.commit()


# Format ke Rupiah, contohnya 1000 → “Rp 1.000,00”
@app.template_filter('rupiah')
def format_rupiah(value):
    try:
        v = float(value)
        return "Rp {:,.2f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "Rp 0,00"

# Format ke kilogram, contohnya 2.5 → “2.5 kg”
def format_kg(value):
    try:
        return f"{float(value):g} kg"
    except (ValueError, TypeError):
        return value

# Format ke meter-persegi, contohnya 100 → “100 m²”
def format_m2(value):
    try:
        return f"{float(value):g} m²"
    except (ValueError, TypeError):
        return value
    
app.jinja_env.filters['kg']     = format_kg
app.jinja_env.filters['m2']     = format_m2

with app.app_context():
    db.create_all()
with app.app_context():
    # jika belum ada akun, buat dengan saldo awal = (pendapatan - biaya) + wisata
    if not Account.query.first():
        # hitung di sini (gunakan logic yang sudah ada)
        production = ProductionCost.query.all()
        revenue    = Revenue.query.all()
        tourism    = Tourism.query.all()

        total_biaya      = sum(i.land_area + i.seed_cost + ... for i in production)
        total_pendapatan = sum(i.price_per_kg * i.strawberry_amount for i in revenue)
        total_wisata     = sum(i.ticket_price * i.visitor_count for i in tourism)

        starting = (total_pendapatan - total_biaya) + total_wisata
        db.session.add(Account(current_balance=starting))
        db.session.commit()


@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# Production Cost CRUD
@app.route('/production')
def production_list():
    items = ProductionCost.query.all()
    return render_template('production.html', items=items)

from flask import flash

from flask import flash

@app.route('/production/add', methods=['GET','POST'])
def production_add():
    if request.method == 'POST':
        data = request.form

        # date validation & parse
        date_str = data.get('date', '').strip()
        if not date_str:
            flash("Tanggal wajib diisi!", "error")
            return redirect(url_for('production_add'))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash("Format tanggal tidak valid!", "error")
            return redirect(url_for('production_add'))

        # create and save
        item = ProductionCost(
            date             = date_obj,
            land_area        = float(data['land_area']),
            seed_cost        = float(data['seed_cost']),
            fertilizer_cost  = float(data['fertilizer_cost']),
            medicine_cost    = float(data['medicine_cost']),
            equipment_cost   = 0.0,
            labor_cost       = float(data['labor_cost']),
            electricity_cost = float(data['electricity_cost']),
            water_cost       = float(data['water_cost'])
        )
        db.session.add(item)
        db.session.commit()

        # update balance
        cost = (
            item.land_area
            + item.seed_cost
            + item.fertilizer_cost
            + item.medicine_cost
            + item.equipment_cost
            + item.labor_cost
            + item.electricity_cost
            + item.water_cost
        )
        acc = Account.query.first()
        acc.current_balance -= cost
        db.session.commit()

        return redirect(url_for('production_list'))

    return render_template('production_form.html', item=None)

@app.route('/production/edit/<int:id>', methods=['GET','POST'])
def production_edit(id):
    item = ProductionCost.query.get_or_404(id)

    if request.method == 'POST':
        data = request.form

        # 1) ambil dan bersihkan string
        date_str = data.get('date', '').strip()
        if not date_str:
            flash("Tanggal wajib diisi!", "error")
            return redirect(url_for('production_edit', id=id))

        # 2) coba parse
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash("Format tanggal tidak valid!", "error")
            return redirect(url_for('production_edit', id=id))

        # 3) Update fields setelah valid date
        item.date             = date_obj
        item.land_area        = float(data['land_area'])
        item.seed_cost        = float(data['seed_cost'])
        item.fertilizer_cost  = float(data['fertilizer_cost'])
        item.medicine_cost    = float(data['medicine_cost'])
        item.equipment_cost   = 0.0
        item.labor_cost       = float(data['labor_cost'])
        item.electricity_cost = float(data['electricity_cost'])
        item.water_cost       = float(data['water_cost'])

        db.session.commit()
        return redirect(url_for('production_list'))

    return render_template('production_form.html', item=item)

@app.route("/production/delete/<int:id>", methods=["POST"])
def production_delete(id):
    # Kode untuk hapus data
    production = ProductionCost.query.get_or_404(id)
    db.session.delete(production)
    db.session.commit()
    flash("Data berhasil dihapus", "success")
    return redirect(url_for("production_list"))

# Revenue CRUD
@app.route('/revenue')
def revenue_list():
    items = Revenue.query.all()
    return render_template('revenue.html', items=items)

@app.route('/revenue/add', methods=['GET','POST'])
def revenue_add():
    if request.method == 'POST':
        data = request.form

        # date parse
        date_str = data.get('date', '').strip()
        if not date_str:
            flash("Tanggal wajib diisi!", "error")
            return redirect(url_for('revenue_add'))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash("Format tanggal tidak valid!", "error")
            return redirect(url_for('revenue_add'))

        item = Revenue(
            date              = date_obj,
            price_per_kg      = float(data['price_per_kg']),
            strawberry_amount = float(data['strawberry_amount'])
        )
        db.session.add(item)
        db.session.commit()

        # update balance
        income = item.price_per_kg * item.strawberry_amount
        acc = Account.query.first()
        acc.current_balance += income
        db.session.commit()

        return redirect(url_for('revenue_list'))

    return render_template('revenue_form.html', item=None)

@app.route('/revenue/edit/<int:id>', methods=['GET', 'POST'])
def revenue_edit(id):
    item = Revenue.query.get_or_404(id)
    if request.method == 'POST':
        data = request.form
        item.date = datetime.strptime(data['date'], '%Y-%m-%d')
        item.price_per_kg = float(data['price_per_kg'])
        item.strawberry_amount = float(data['strawberry_amount'])
        db.session.commit()
        return redirect(url_for('revenue_list'))
    return render_template('revenue_form.html', item=item)

@app.route('/revenue/delete/<int:id>')
def revenue_delete(id):
    item = Revenue.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('revenue_list'))

# Tourism CRUD
@app.route('/tourism')
def tourism_list():
    items = Tourism.query.all()
    return render_template('tourism.html', items=items)

@app.route('/tourism/add', methods=['GET','POST'])
def tourism_add():
    if request.method == 'POST':
        data = request.form

        # date parse
        date_str = data.get('date', '').strip()
        if not date_str:
            flash("Tanggal wajib diisi!", "error")
            return redirect(url_for('tourism_add'))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            flash("Format tanggal tidak valid!", "error")
            return redirect(url_for('tourism_add'))

        item = Tourism(
            date          = date_obj,
            ticket_price  = float(data['ticket_price']),
            visitor_count = int(data['visitor_count'])
        )
        db.session.add(item)
        db.session.commit()

        # update balance
        income = item.ticket_price * item.visitor_count
        acc = Account.query.first()
        acc.current_balance += income
        db.session.commit()

        return redirect(url_for('tourism_list'))

    return render_template('tourism_form.html', item=None)


@app.route('/tourism/edit/<int:id>', methods=['GET', 'POST'])
def tourism_edit(id):
    item = Tourism.query.get_or_404(id)
    if request.method == 'POST':
        data = request.form
        item.date = datetime.strptime(data['date'], '%Y-%m-%d')
        item.ticket_price = float(data['ticket_price'])
        item.date = datetime.strptime(data['date'], '%Y-%m-%d')
        item.ticket_price = float(data['ticket_price'])
        item.visitor_count = int(data['visitor_count'])
        db.session.commit()
        return redirect(url_for('tourism_list'))
    return render_template('tourism_form.html', item=item)

@app.route('/tourism/delete/<int:id>')
def tourism_delete(id):
    item = Tourism.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('tourism_list'))

# ——— CRUD JURNAL UMUM ————————————————————————————————————————————
# ---- CRUD JURNAL UMUM ----
REVENUE_ACCOUNTS = ['Penjualan']
EXPENSE_ACCOUNTS = ['Beban', 'Beban Sewa', 'Beban Iklan', 'Beban Angkut Penjualan']

@app.route('/journal')
def journal_list():
    transactions = Transaction.query.options(joinedload(Transaction.entries)).order_by(Transaction.date).all()
    
    total_debet = sum(
        entry.amount 
        for txn in transactions 
        for entry in txn.entries 
        if entry.entry_type == 'debit'
    )
    total_kredit = sum(
        entry.amount 
        for txn in transactions 
        for entry in txn.entries 
        if entry.entry_type == 'kredit'
    )
    
    return render_template(
        'journal_list.html',
        transactions=transactions,
        total_debet=total_debet,
        total_kredit=total_kredit
    )

@app.route('/journal/add', methods=['GET', 'POST'])
def journal_add():
    if request.method == 'POST':
        try:
            # Ambil data dari form
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            description = request.form['description'].strip()
            accounts = request.form.getlist('account[]')
            entry_types = request.form.getlist('entry_type[]')  # Nama field diperbaiki
            amounts = request.form.getlist('amount[]')

            # Validasi
            if len(accounts) < 2:
                flash('Minimal 2 entri diperlukan!', 'error')
                return redirect(request.url)

            # Proses entries
            entries = []
            debit_total = 0
            credit_total = 0
            for account, entry_type, amt in zip(accounts, entry_types, amounts):
                account = account.strip()
                if not account or not entry_type or not amt:
                    flash('Semua field harus diisi!', 'error')
                    return redirect(request.url)
                
                try:
                    amount = float(amt)
                except ValueError:
                    flash('Nominal harus angka!', 'error')
                    return redirect(request.url)
                
                if entry_type == 'debit':
                    debit_total += amount
                else:
                    credit_total += amount
                
                entries.append((account, entry_type, amount))

            # Validasi balance
            if debit_total != credit_total:
                flash(f'Debit: {debit_total:,} ≠ Kredit: {credit_total:,}', 'error')
                return redirect(request.url)

            # Simpan transaksi
            txn = Transaction(date=date, description=description)
            db.session.add(txn)
            
            # Simpan entri
            acc = Account.query.first()
            for account, entry_type, amount in entries:
                entry = JournalEntry(
                    account=account,
                    entry_type=entry_type,  # Pastikan nama field sesuai
                    amount=amount,
                    transaction=txn
                )
                db.session.add(entry)
                
                # Update saldo
                if account in REVENUE_ACCOUNTS and entry_type == 'kredit':
                    acc.current_balance += amount
                elif account in EXPENSE_ACCOUNTS and entry_type == 'debit':
                    acc.current_balance -= amount
            
            db.session.commit()
            flash('Transaksi berhasil disimpan!', 'success')
            return redirect(url_for('journal_list'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('journal_form.html', transaction=None)

@app.route('/journal/edit/<int:id>', methods=['GET', 'POST'])
def journal_edit(id):
    txn = Transaction.query.get_or_404(id)
    acc = Account.query.first()

    if request.method == 'POST':
        try:
            # Rollback saldo lama
            for entry in txn.entries:
                if entry.account in REVENUE_ACCOUNTS and entry.entry_type == 'kredit':
                    acc.current_balance -= entry.amount
                elif entry.account in EXPENSE_ACCOUNTS and entry.entry_type == 'debit':
                    acc.current_balance += entry.amount

            # Ambil data baru
            entry_ids = request.form.getlist('entry_id[]')
            accounts = request.form.getlist('account[]')
            entry_types = request.form.getlist('entry_type[]')  # Pastikan nama ini
            amounts = request.form.getlist('amount[]')

            # Validasi
            if len(accounts) < 2:
                flash('Minimal 2 entri diperlukan!', 'error')
                return redirect(request.url)

            # Proses entri
            new_entries = []
            debit_total = 0
            credit_total = 0
            
            for idx, (entry_id, account, entry_type, amt) in enumerate(zip(entry_ids, accounts, entry_types, amounts)):
                account = account.strip()
                if not account or not entry_type or not amt:
                    flash('Semua field harus diisi!', 'error')
                    return redirect(request.url)
                
                try:
                    amount = float(amt)
                except ValueError:
                    flash('Nominal harus angka!', 'error')
                    return redirect(request.url)
                
                # Update existing entry
                if entry_id:
                    entry = JournalEntry.query.get(entry_id)
                    entry.account = account
                    entry.entry_type = entry_type  # Pastikan pakai entry_type
                    entry.amount = amount
                else: # New entry
                    entry = JournalEntry(
                        account=account,
                        entry_type=entry_type,
                        amount=amount,
                        transaction_id=txn.id
                    )
                    db.session.add(entry)
                
                # Hitung total
                if entry_type == 'debit':
                    debit_total += amount
                else:
                    credit_total += amount
                
                new_entries.append(entry)

            # Hapus entri yang tidak ada di form
            for entry in txn.entries:
                if entry not in new_entries:
                    db.session.delete(entry)

            # Validasi balance
            if debit_total != credit_total:
                flash(f'Debit: {debit_total:,} ≠ Kredit: {credit_total:,}', 'error')
                return redirect(request.url)

            # Update saldo baru
            for entry in new_entries:
                if entry.account in REVENUE_ACCOUNTS and entry.entry_type == 'kredit':
                    acc.current_balance += entry.amount
                elif entry.account in EXPENSE_ACCOUNTS and entry.entry_type == 'debit':
                    acc.current_balance -= entry.amount

            db.session.commit()
            flash('Transaksi berhasil diupdate!', 'success')
            return redirect(url_for('journal_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('journal_form.html', transaction=txn)

@app.route('/journal/delete/<int:id>', methods=['POST'])
def journal_delete(id):
    txn = Transaction.query.get_or_404(id)
    acc = Account.query.first()
    
    try:
        # Rollback saldo
        for entry in txn.entries:
            if entry.account in REVENUE_ACCOUNTS and entry.type == 'kredit':
                acc.current_balance -= entry.amount
            elif entry.account in EXPENSE_ACCOUNTS and entry.type == 'debit':
                acc.current_balance += entry.amount
        
        db.session.delete(txn)
        db.session.commit()
        flash('Transaksi dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('journal_list'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)