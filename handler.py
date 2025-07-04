import hashlib
import pytz
import random
import string
from datetime import datetime
from math import ceil
# from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from flask import current_app
from flask_mail import Mail, Message
from sqlalchemy.orm import joinedload
from .models import db, Event, Ticket, User

class Handler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Handler, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        pass

    def generate_unique_event_id(self):
        
        return 1

    def add_event(self, event_name, event_datetime, event_end_datetime, event_location, event_description, ticket_distribution_start_datetime, is_ticket_distribution_permitted, number_of_tickets, department, professor_name, event_type):
        try:
            with current_app.app_context():
                event_id = self.generate_unique_event_id()
                if not event_id:
                    print("Failed to generate unique event ID.")
                    return False
                else:
                    new_event = Event(
                        event_id=event_id,
                        event_name=event_name,
                        event_datetime=event_datetime,
                        event_end_datetime=event_end_datetime,
                        event_location=event_location,
                        event_description=event_description,
                        ticket_distribution_start_datetime=ticket_distribution_start_datetime,
                        is_ticket_distribution_permitted=is_ticket_distribution_permitted,
                        number_of_tickets=number_of_tickets,
                        number_of_remaining_tickets=number_of_tickets,
                        department=department,
                        professor_name=professor_name,
                        event_type=event_type
                    )
                    db.session.add(new_event)
                    db.session.commit()
                    return True
        except IntegrityError:
            db.session.rollback()
            print(f"Event ID {event_id} already exists.")
            return False
        except Exception as e:
            print(f"Error adding event: {e}")
            return False

    def remove_event(self, event_id):
        try:
            with current_app.app_context():
                # バルク削除: チケットを一括削除（DBのON DELETE CASCADEも有効）
                Ticket.query.filter_by(event_id=event_id).delete(synchronize_session=False)
                # イベント本体も削除
                Event.query.filter_by(event_id=event_id).delete(synchronize_session=False)
                db.session.commit()
                # セッションの内容をリフレッシュ（他のインスタンスやワーカーでも整合性を保つ）
                db.session.expire_all()
                return True
        except IntegrityError:
            db.session.rollback()
            print(f"Event ID {event_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error removing event: {e}")
            return False


    def update_event(self, event_id, event_name=None, event_datetime=None, event_end_datetime=None, event_location=None, event_description=None, ticket_distribution_start_datetime=None, is_ticket_distribution_permitted=None, number_of_tickets=None, department=None, professor_name=None, event_type=None):
        try:
            with current_app.app_context():
                event = Event.query.filter_by(event_id=event_id).first()
                if event:
                    if event_name is not None:
                        event.event_name = event_name
                    if event_datetime is not None:
                        event.event_datetime = event_datetime
                    if event_end_datetime is not None:
                        event.event_end_datetime = event_end_datetime
                    if event_location is not None:
                        event.event_location = event_location
                    if event_description is not None:
                        event.event_description = event_description
                    if ticket_distribution_start_datetime is not None:
                        event.ticket_distribution_start_datetime = ticket_distribution_start_datetime
                    if is_ticket_distribution_permitted is not None:
                        event.is_ticket_distribution_permitted = is_ticket_distribution_permitted
                    if number_of_tickets is not None:
                        number_of_published_tickets = event.number_of_tickets - event.number_of_remaining_tickets
                        event.number_of_tickets = number_of_tickets
                        event.number_of_remaining_tickets = int(number_of_tickets) - number_of_published_tickets
                    if department is not None:
                        event.department = department
                    if professor_name is not None:
                        event.professor_name = professor_name
                    if event_type is not None:
                        event.event_type = event_type
                    db.session.commit()
                    return True
                else:
                    print(f"Event with ID {event_id} not found.")
                    return False
        except IntegrityError:
            db.session.rollback()
            print(f"Event ID {event_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error updating event: {e}")
            return False

    def generate_unique_ticket_id(self, event_id):
       
            return 1

    def publish_ticket(self, owner_id, event_id, is_forced=False):
        try:
            with current_app.app_context():
                event = Event.query.filter_by(event_id=event_id).first()
                japan_tz = pytz.timezone('Asia/Tokyo')
                ticket_distribution_start_datetime = japan_tz.localize(datetime.strptime(event.ticket_distribution_start_datetime, '%Y-%m-%dT%H:%M'))
                if event and event.is_ticket_distribution_permitted and ticket_distribution_start_datetime <= datetime.now(japan_tz):
                    if not is_forced and event.number_of_remaining_tickets <= 0:
                        print(f"No remaining tickets for event ID {event_id}.")
                        return 'no_remaining'
                    else:
                        if event.number_of_remaining_tickets > 0:
                            event.number_of_remaining_tickets -= 1
                        elif is_forced and event.number_of_remaining_tickets <= 0:
                            event.number_of_tickets += 1
                        ticket_id = self.generate_unique_ticket_id(event_id)
                        if not ticket_id:
                            print("Failed to generate unique ticket ID.")
                            return 'error'
                        else:
                            new_ticket = Ticket(ticket_id=ticket_id, owner_id=owner_id, event_id=event_id, is_used=False)
                            db.session.add(new_ticket)
                            db.session.commit()
                            return True
                else:
                    if not event:
                        print(f"Event with ID {event_id} not found.")
                        return 'not_found'
                    elif not event.is_ticket_distribution_permitted:
                        print(f"Tickets for event ID {event_id} are not permitted.")
                        return 'not_permitted'
                    elif event.number_of_remaining_tickets <= 0:
                        print(f"No remaining tickets for event ID {event_id}.")
                        return 'no_remaining'
                    print(f"Unable to publish ticket for event ID {event_id}.")
                    return 'error'
        except IntegrityError:
            db.session.rollback()
            print(f"Ticket ID {ticket_id} already exists.")
            return 'error'
        except Exception as e:
            print(f"Error publishing ticket: {e}")
            return 'error'

    def cancel_ticket(self, event_id, owner_id, ticket_id=None):
        try:
            with current_app.app_context():
                if ticket_id:
                    ticket_to_cancel = Ticket.query.filter_by(event_id=event_id, owner_id=owner_id, ticket_id=ticket_id).first()
                    if ticket_to_cancel:
                        event = Event.query.filter_by(event_id=event_id).first()
                        if event and not ticket_to_cancel.is_used:
                            event.number_of_remaining_tickets += 1
                        db.session.delete(ticket_to_cancel)
                        db.session.commit()
                        return True
                else:
                    tickets_to_cancel = Ticket.query.filter_by(event_id=event_id, owner_id=owner_id).first()
                    if tickets_to_cancel:
                        ticket_to_cancel = max(tickets_to_cancel, key=lambda t: t.ticket_id)
                        event = Event.query.filter_by(event_id=event_id).first()
                        if event and not ticket_to_cancel.is_used:
                            event.number_of_remaining_tickets += 1
                        db.session.delete(ticket_to_cancel)
                        db.session.commit()
                        return True
                    else:
                        print(f"No tickets found for event ID {event_id} and owner ID {owner_id}.")
                        return False
        except IntegrityError:
            db.session.rollback()
            print(f"Ticket ID {ticket_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error canceling ticket: {e}")
            return False

    def get_events_list_as_json(self):
        events = db.session.query(
            Event.event_id, Event.event_name, Event.event_datetime, Event.event_end_datetime,
            Event.event_location, Event.department, Event.professor_name, Event.event_type,
            Event.event_description, Event.ticket_distribution_start_datetime,
            Event.is_ticket_distribution_permitted, Event.number_of_tickets, Event.number_of_remaining_tickets
        ).all()
        return [
            {
                'event_id': event.event_id,
                'event_name': event.event_name,
                'event_datetime': event.event_datetime,
                'event_end_datetime': event.event_end_datetime,
                'event_location': event.event_location,
                'department': event.department,
                'professor_name': event.professor_name,
                'event_type': event.event_type,
                'event_description': event.event_description,
                'ticket_distribution_start_datetime': event.ticket_distribution_start_datetime,
                'is_ticket_distribution_permitted': event.is_ticket_distribution_permitted,
                'number_of_tickets': event.number_of_tickets,
                'number_of_remaining_tickets': event.number_of_remaining_tickets
            } for event in events
        ]
    def get_tickets_list_as_json(self, owner_id):
        try:
            with current_app.app_context():
                tickets = Ticket.query.options(joinedload(Ticket.event)).filter_by(owner_id=owner_id).all()
                return [
                    {
                        'ticket_id': ticket.ticket_id,
                        'event_id': ticket.event_id,
                        'event_name': ticket.event.event_name if ticket.event else None,
                        'event_datetime': ticket.event.event_datetime if ticket.event else None,
                        'event_end_datetime': ticket.event.event_end_datetime if ticket.event else None,
                        'event_location': ticket.event.event_location if ticket.event else None,
                        'department': ticket.event.department if ticket.event else None,
                        'professor_name': ticket.event.professor_name if ticket.event else None,
                        'event_type': ticket.event.event_type if ticket.event else None,
                        'event_description': ticket.event.event_description if ticket.event else None,
                        'is_used': ticket.is_used,
                    } for ticket in tickets
                ]
        except Exception as e:
            print(f"Error getting tickets list: {e}")
            return None

    def generate_unique_user_id(self):
        
        return None

    def update_user_data(self, user_id, password=None, is_admin=None, email_address=None):
        try:
            with current_app.app_context():
                user = User.query.filter_by(user_id=user_id).first()
                if user:
                    if password is not None:
                        user.password = hashlib.sha256(password.encode()).hexdigest()
                    if is_admin is not None:
                        if user_id == 'SrvAcc':
                            user.is_admin = True
                        else:
                            user.is_admin = is_admin
                    if email_address is not None:
                        user.email_address = email_address.strip()
                    db.session.commit()
                    return True
                else:
                    print(f"User with ID {user_id} not found.")
                    return False
        except IntegrityError:
            db.session.rollback()
            print(f"User ID {user_id} already exists.")
            return False
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    def get_default_password_str(self, user_id):
       
       
            return None

    def get_default_password_hash(self, user_id):
        try:
            return hashlib.sha256(self.get_default_password_str(user_id).encode()).hexdigest()
        except Exception as e:
            print(f"Error hashing default password: {e}")
            return None

    def create_user(self, user_id=None, email_address=None):
        try:
            with current_app.app_context():
                if user_id is not None:
                    existing_user = User.query.filter_by(user_id=user_id).first()
                    if existing_user:
                        print(f"User with ID {user_id} already exists.")
                        return None
                    else:
                        db.session.add(User(user_id=user_id, password=self.get_default_password_hash(user_id), is_admin=False, email_address=email_address))
                        db.session.commit()
                        return user_id
                else:
                    user_id = self.generate_unique_user_id()
                if not user_id:
                    print("Failed to generate unique user ID.")
                    return None
                else:
                    db.session.add(User(user_id=user_id, password=self.get_default_password_hash(user_id), is_admin=False, email_address=email_address))
                    db.session.commit()
                    return user_id
        except IntegrityError:
            db.session.rollback()
            print(f"User ID {user_id} already exists.")
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def delete_user(self, user_id):
        try:
            with current_app.app_context():
                if user_id == 'SrvAcc':
                    print("Cannot delete the default user.")
                    return False
                # 1. 削除前に未使用チケットをイベントごとに集計
                tickets = Ticket.query.filter_by(owner_id=user_id, is_used=False).all()
                event_ticket_count = {}
                for t in tickets:
                    event_ticket_count[t.event_id] = event_ticket_count.get(t.event_id, 0) + 1
                # 2. イベントの残数を復活
                for event_id, cnt in event_ticket_count.items():
                    event = Event.query.filter_by(event_id=event_id).first()
                    if event:
                        event.number_of_remaining_tickets += cnt
                # 3. バルク削除: チケットを一括削除
                Ticket.query.filter_by(owner_id=user_id).delete(synchronize_session=False)
                # 4. ユーザー本体も削除
                User.query.filter_by(user_id=user_id).delete(synchronize_session=False)
                db.session.commit()
                db.session.expire_all()
                return True
        except IntegrityError:
            db.session.rollback()
            print(f"User ID {user_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    def reset_user(self, user_id):
        try:
            with current_app.app_context():
                self.update_user_data(user_id, password=self.get_default_password_hash(user_id), is_admin=False)
                return True
        except Exception as e:
            print(f"Error resetting user: {e}")
            return False


    def login(self, user_id, password):
        try:
            with current_app.app_context():
                if user_id == 'SrvAcc' and not User.query.filter_by(user_id=user_id).first():
                    db.session.add(User(user_id=user_id, password=self.get_default_password_hash(user_id), is_admin=True, email_address='rikoten.jikkenkou@gmail.com'))
                    db.session.commit()
                user = User.query.filter_by(user_id=user_id).first()
                if user:
                    if user.password == hashlib.sha256(password.encode()).hexdigest():
                        return True
                    else:
                        print(f"Invalid password for user ID {user_id}.")
                        return False
                else:
                    print(f"User with ID {user_id} not found.")
                    return False
        except IntegrityError:
            db.session.rollback()
            print(f"Failed to log in user ID {user_id}.")
            return False
        except Exception as e:
            print(f"Error logging in: {e}")
            return False

    def get_session_token(self, user_id):
       
        return None

    def get_user_data_list_as_json(self, page=1, per_page=50):
        users = User.query.options(joinedload(User.tickets)).paginate(page=page, per_page=per_page, error_out=False).items
        return [
            {
                'user_id': user.user_id,
                'is_admin': user.is_admin,
                'owning_tickets': [
                    {
                        'ticket_id': ticket.ticket_id,
                        'event_id': ticket.event_id,
                        'event_name': ticket.event.event_name if ticket.event else None,
                        'event_datetime': ticket.event.event_datetime if ticket.event else None,
                        'event_end_datetime': ticket.event.event_end_datetime if ticket.event else None,
                        'event_location': ticket.event.event_location if ticket.event else None,
                        'department': ticket.event.department if ticket.event else None,
                        'professor_name': ticket.event.professor_name if ticket.event else None,
                        'event_type': ticket.event.event_type if ticket.event else None,
                        'event_description': ticket.event.event_description if ticket.event else None,
                        'is_used': ticket.is_used,
                    } for ticket in user.tickets
                ]
            } for user in users
        ]

    def use_ticket(self, event_id, ticket_id, password):
        try:
            with current_app.app_context():
                ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
                if self.get_event_checkin_password(event_id) == password:
                    if ticket and not ticket.is_used:
                        ticket.is_used = True
                        db.session.commit()
                        return True
                    else:
                        print(f"Ticket with ID {ticket_id} is already used or not found.")
                        return False
                else:
                    print(f"Invalid password for event ID {event_id}.")
                    return False
        except IntegrityError:
            db.session.rollback()
            print(f"Ticket ID {ticket_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error using ticket: {e}")
            return False

    def use_paper_ticket(self, ticket_id):
        try:
            with current_app.app_context():
                ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
                if ticket and ticket.owner_id != 'UPaper':
                    print(f"Ticket with ID {ticket_id} is not a paper ticket.")
                    return False
                if not ticket.is_used:
                    ticket.is_used = True
                    db.session.commit()
                    return True
                else:
                    print(f"Ticket with ID {ticket_id} is already used.")
                    return False
        except IntegrityError:
            db.session.rollback()
            print(f"Ticket ID {ticket_id} does not exist.")
            return False
        except Exception as e:
            print(f"Error using paper ticket: {e}")
            return False

    def cancel_all_unused_tickets(self, event_id):
        try:
            # バルク削除: 未使用チケットを一括削除
            q = Ticket.query.filter_by(event_id=event_id, is_used=False).filter(Ticket.owner_id != 'UPaper')
            count = q.count()
            q.delete(synchronize_session=False)
            event = Event.query.filter_by(event_id=event_id).first()
            if event:
                event.number_of_remaining_tickets += count
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            print(f"Failed to cancel tickets for event ID {event_id}.")
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error canceling all unused tickets: {e}")
            return False

    def get_event_checkin_password(self, event_id):
        try:
            with current_app.app_context():
                event = Event.query.filter_by(event_id=event_id).first()
                if event:
                    random.seed(hashlib.sha256(event_id.encode()).hexdigest())
                    return ''.join(random.choice(string.digits) for _ in range(2))
                else:
                    print(f"Event with ID {event_id} not found.")
                    return None
        except Exception as e:
            print(f"Error getting event check-in password: {e}")
            return None

    def publish_paper_ticket(self, event_id, is_forced=False):
        try:
            with current_app.app_context():
                user = User.query.filter_by(user_id='UPaper').first()
                if not user:
                    self.create_user('UPaper')
                ticket_id = self.publish_ticket('UPaper', event_id, is_forced)
                if not ticket_id:
                    print("Failed to publish paper ticket.")
                    return False
                ticket = Ticket.query.filter_by(ticket_id=ticket_id).first()
                if not ticket:
                    print(f"Ticket with ID {ticket_id} not found.")
                    return False
                # 1枚分のみ辞書で返す
                return {
                    'ticket_id': ticket.ticket_id,
                    'event_id': ticket.event_id,
                    'event_name': ticket.event.event_name,
                    'event_datetime': ticket.event.event_datetime,
                    'event_end_datetime': ticket.event.event_end_datetime,
                    'event_location': ticket.event.event_location,
                    'department': ticket.event.department,
                    'professor_name': ticket.event.professor_name,
                    'event_type': ticket.event.event_type,
                }
        except Exception as e:
            print(f"Error publishing paper ticket: {e}")
            return False
    
    def send_email(self, user_id, subject, body):
        app = current_app
        app.config.update(
            MAIL_SERVER='smtp.gmail.com',  # GmailのSMTPサーバー
            MAIL_PORT=587,                # ポート番号
            MAIL_USE_TLS=True,            # TLSを使用
            MAIL_USERNAME='rikoten.jikkenkou@gmail.com',  # Gmailアカウント
            MAIL_PASSWORD='hvfoabjqnncdnwmh'         # アプリパスワード
        )
        mail = Mail(app) 
        try:
            if not user_id:
                print("User ID is empty.")
                return False
            if not subject:
                print("Subject is empty.")
                return False
            if not body:
                print("Body is empty.")
                return False
            if not mail:
                print("Mail instance is not initialized.")
                return False
    
            with app.app_context():
                user = User.query.filter_by(user_id=user_id).first()
                if not user:
                    print(f"User with ID {user_id} not found.")
                    return False
                email_address = user.email_address
                if not email_address:
                    print(f"User with ID {user_id} does not have an email address.")
                    return False
                msg = Message(subject=subject, sender="rikoten.jikkenkou@gmail.com", recipients=[email_address])
                msg.body = body
                mail.send(msg)
                print(f"Email sent to {email_address} with subject: {subject}")
                return True
        except Exception as e:
            print(f"Error initializing mail: {e}")
            return False
    
    def send_bulk_email(self, subject, body, is_to_all_users=False, event_id=None, is_to_event_nonholders=False, per_page=100):
        try:
            with current_app.app_context():
                page = 1
                while True:
                    # クエリをページごとに取得
                    if event_id and is_to_event_nonholders:
                        holders = set([row[0] for row in db.session.query(Ticket.owner_id).filter(Ticket.event_id==event_id).distinct().all()])
                        query = User.query.filter(~User.user_id.in_(holders))
                    elif is_to_all_users:
                        query = User.query
                    elif event_id:
                        holders = set([row[0] for row in db.session.query(Ticket.owner_id).filter(Ticket.event_id==event_id).distinct().all()])
                        query = User.query.filter(User.user_id.in_(holders))
                    else:
                        return False
    
                    users_page = query.paginate(page=page, per_page=per_page, error_out=False)
                    if not users_page.items:
                        break
                    for user in users_page.items:
                        if user.email_address:
                            self.send_email(user.user_id, subject, body)
                    if not users_page.has_next:
                        break
                    page += 1
            return True
        except Exception as e:
            print(f"Error sending emails: {e}")
            return False

    def publish_tickets_bulk(self, owner_id, event_id, ticket_count, is_forced=False):
        """
        絶対に重複・超過を防ぐバルク発行。イベント行をFOR UPDATEでロックし、
        残数チェック・減算・チケットID一括生成・バルク挿入をトランザクション内で行う。
        """
        from sqlalchemy import select
        try:
            with current_app.app_context():
                # イベント行を排他ロック
                event = db.session.execute(
                    select(Event).where(Event.event_id == event_id).with_for_update()
                ).scalar_one_or_none()
                if not event:
                    print(f"Event with ID {event_id} not found.")
                    return False, 'not_found'
                japan_tz = pytz.timezone('Asia/Tokyo')
                ticket_distribution_start_datetime = japan_tz.localize(datetime.strptime(event.ticket_distribution_start_datetime, '%Y-%m-%dT%H:%M'))
                if not event.is_ticket_distribution_permitted:
                    print(f"Tickets for event ID {event_id} are not permitted.")
                    return False, 'not_permitted'
                if ticket_distribution_start_datetime > datetime.now(japan_tz):
                    print(f"Ticket distribution not started yet for event ID {event_id}.")
                    return False, 'not_started'
                # 残数チェック
                if not is_forced and event.number_of_remaining_tickets < ticket_count:
                    print(f"Not enough tickets for event ID {event_id}.")
                    return False, 'no_remaining'
                # チケットID一括生成
                existing_ids = {t.ticket_id for t in Ticket.query.filter_by(event_id=event_id).all()}
                new_tickets = []
                for i in range(1, 4096):
                    ticket_id = f"{event_id}T{i:03x}"
                    if ticket_id not in existing_ids:
                        new_tickets.append(ticket_id)
                        if len(new_tickets) == ticket_count:
                            break
                if len(new_tickets) < ticket_count:
                    print("Failed to generate enough unique ticket IDs.")
                    return False, 'id_error'
                # 残数減算
                if not is_forced:
                    event.number_of_remaining_tickets -= ticket_count
                elif is_forced and event.number_of_remaining_tickets < ticket_count:
                    event.number_of_tickets += (ticket_count - event.number_of_remaining_tickets)
                    event.number_of_remaining_tickets = 0
                # バルク挿入
                ticket_objs = [Ticket(ticket_id=tid, owner_id=owner_id, event_id=event_id, is_used=False) for tid in new_tickets]
                db.session.bulk_save_objects(ticket_objs)
                db.session.commit()
                db.session.expire_all()
                return True, new_tickets
        except IntegrityError as e:
            db.session.rollback()
            print(f"IntegrityError: {e}")
            return False, 'integrity_error'
        except Exception as e:
            db.session.rollback()
            print(f"Error in publish_tickets_bulk: {e}")
            return False, 'error'

    def is_admin(self, user_id):
        with current_app.app_context():
            user = User.query.filter_by(user_id=user_id).first()
            return user.is_admin if user else False