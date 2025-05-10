from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ProductionCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    land_area = db.Column(db.Float, nullable=False)
    seed_cost = db.Column(db.Float, nullable=False)
    fertilizer_cost = db.Column(db.Float, nullable=False)
    medicine_cost = db.Column(db.Float, nullable=False)
    equipment_cost = db.Column(db.Float, nullable=False)
    labor_cost = db.Column(db.Float, nullable=False)
    electricity_cost = db.Column(db.Float, nullable=False)
    water_cost = db.Column(db.Float, nullable=False)

class Revenue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)
    strawberry_amount = db.Column(db.Float, nullable=False)

class Tourism(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False)
    visitor_count = db.Column(db.Integer, nullable=False, default=0)

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    current_balance = db.Column(db.Float, nullable=False, default=0.0)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    
    entries = db.relationship(
        'JournalEntry',
        back_populates='transaction',
        cascade='all, delete-orphan'
    )

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(50), nullable=False)
    entry_type = db.Column(db.String(10), nullable=False)  # Pastikan nama ini
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(
        db.Integer, 
        db.ForeignKey('transactions.id', ondelete='CASCADE'),
        nullable=False
    )
    
    transaction = db.relationship('Transaction', back_populates='entries')