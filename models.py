from . import db

class Event(db.Model):
    __tablename__ = 'events'
    __table_args__ = (
        db.Index('ix_event_event_id', 'event_id'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.String(4), unique=True, nullable=False)
    event_name = db.Column(db.String(50), nullable=False)
    event_datetime = db.Column(db.String(16), nullable=False)
    event_end_datetime = db.Column(db.String(16), nullable=False)
    event_location = db.Column(db.String(20), nullable=False)
    event_description = db.Column(db.Text, nullable=False)
    ticket_distribution_start_datetime = db.Column(db.String(16), nullable=False)
    is_ticket_distribution_permitted = db.Column(db.Boolean, nullable=False)
    number_of_tickets = db.Column(db.Integer, nullable=False)
    number_of_remaining_tickets = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(15), nullable=False)
    professor_name = db.Column(db.String(40), nullable=False)
    event_type = db.Column(db.String(10), nullable=False) 
    tickets = db.relationship('Ticket', backref='event', lazy=True)

class Ticket(db.Model):
    __tablename__ = 'tickets'
    __table_args__ = (
        db.Index('ix_ticket_ticket_id', 'ticket_id'),
        db.Index('ix_ticket_owner_id', 'owner_id'),
        db.Index('ix_ticket_event_id', 'event_id'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_id = db.Column(db.String(8), unique=True, nullable=False)
    owner_id = db.Column(db.String(6), db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.String(4), db.ForeignKey('events.event_id', ondelete='CASCADE'), nullable=False)
    is_used = db.Column(db.Boolean, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.Index('ix_user_user_id', 'user_id'),
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(6), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    email_address = db.Column(db.String(50), nullable=True)
    tickets = db.relationship('Ticket', backref='owner', lazy=True)
    # is_admin: Trueなら管理者、Falseなら一般ユーザー