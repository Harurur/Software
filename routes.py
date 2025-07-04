# user_id=SrvAccは最初に権限を与えるためのアカウントなので権限レベルは3だが権限が必要な関数は実行させない
from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify, make_response, send_from_directory

import os

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html'), 200

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(main.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    handler = current_app.config['handler']
    success = handler.login(user_id, password)
    if success:
        session_token = handler.get_session_token(user_id)
        is_admin = handler.is_admin(user_id)
        if is_admin:
            redirect_url = url_for('main.admin', user_id=user_id)
        else:
            redirect_url = url_for('main.user', user_id=user_id)
        response = make_response(jsonify({'redirect_url': redirect_url}), 200)
        response.set_cookie('user_id', user_id, max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
        response.set_cookie('session_token', session_token, max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
        response.set_cookie('the_day_user', 'False', max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
        return response
    return '', 403

@main.route('/signup_for_the_day', methods=['POST'])
def signup_for_the_day():
    # handler = current_app.config['handler']
    # user_id  = handler.create_user()
    # session_token = handler.get_session_token(user_id)
    # redirect_url = url_for('main.user', user_id=user_id + '~')
    # response = make_response(jsonify({'redirect_url': redirect_url}), 200)
    # response.set_cookie('user_id', user_id, max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
    # response.set_cookie('session_token', session_token, max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
    # response.set_cookie('the_day_user', 'True', max_age=60*60*24, httponly=True, secure=True, samesite='Strict')
    # return response
    return '', 501  # Not Implemented

@main.route('/check_cookie')
def check_cookie():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')

    if user_id and session_token:
        return '', 200
    else:
        return '', 401

@main.route('/login_with_session_token')
def login_with_session_token():
    user_id = request.cookies.get('user_id')
    session_token = request.cookies.get('session_token')
    the_day_user = request.cookies.get('the_day_user')
    handler = current_app.config['handler']
    if handler.get_session_token(user_id) == session_token:
        is_admin = handler.is_admin(user_id)
        if is_admin:
            return redirect(url_for('main.admin', user_id=user_id)), 302
        else:
            if the_day_user == 'True':
                return redirect(url_for('main.user', user_id=user_id + '~')), 302
            else:
                return redirect(url_for('main.user', user_id=user_id)), 302
    else:
        response = make_response(redirect(url_for('main.index')))
        response.delete_cookie('user_id', httponly=True, secure=True, samesite='Strict')
        response.delete_cookie('session_token', httponly=True, secure=True, samesite='Strict')
        response.delete_cookie('the_day_user', httponly=True, secure=True, samesite='Strict')
        return response

@main.route('/logout')
def logout():
    response = make_response(redirect(url_for('main.index')))
    response.delete_cookie('user_id', httponly=True, secure=True, samesite='Strict')
    response.delete_cookie('session_token', httponly=True, secure=True, samesite='Strict')
    response.delete_cookie('the_day_user', httponly=True, secure=True, samesite='Strict')
    return response

@main.route('/admin/<string:user_id>')
def admin(user_id):
    handler = current_app.config['handler']
    session_token = request.cookies.get('session_token')
    if session_token and handler.get_session_token(user_id) == session_token:
        if user_id == 'SrvAcc':
            return render_template('srv_acc.html', user_id=user_id), 200
        if handler.is_admin(user_id):
            return render_template('admin.html', user_id=user_id), 200
    return redirect(url_for('main.index')), 302

@main.route('/user/<string:user_id>')
def user(user_id):
    handler = current_app.config['handler']
    session_token = request.cookies.get('session_token')
    if user_id.endswith('~'):
        user_id_normalized = user_id[:-1]
    else:
        user_id_normalized = user_id
    if session_token and handler.get_session_token(user_id_normalized) == session_token:
        if not handler.is_admin(user_id_normalized):
            return render_template('user.html', user_id=user_id_normalized), 200
    return redirect(url_for('main.index')), 302

@main.route('/add_event', methods=['POST'])
def add_event():
    data = request.get_json()
    event_name = data.get('event_name')
    event_datetime = data.get('event_datetime')
    event_end_datetime = data.get('event_end_datetime')
    event_location = data.get('event_location')
    event_description = data.get('event_description')
    ticket_distribution_start_datetime = data.get('ticket_distribution_start_datetime')
    is_ticket_distribution_permitted = data.get('is_ticket_distribution_permitted', 'false').lower() == 'true'
    number_of_tickets = data.get('number_of_tickets')
    department = data.get('department')
    professor_name = data.get('professor_name')
    event_type = data.get('event_type')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']

    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.add_event(event_name, event_datetime, event_end_datetime, event_location, event_description, ticket_distribution_start_datetime, is_ticket_distribution_permitted, number_of_tickets, department, professor_name, event_type)

    if success:
        return '', 200
    else:
        return '', 403

@main.route('/get_events_list')
def get_events_list():
    handler = current_app.config['handler']
    events = handler.get_events_list_as_json()
    if events is None:
        return '', 404
    return jsonify({'events': events}), 200

@main.route('/update_event/', methods=['POST'])
def update_event():
    data = request.get_json()
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_datetime = data.get('event_datetime')
    event_end_datetime = data.get('event_end_datetime')
    event_location = data.get('event_location')
    event_description = data.get('event_description')
    ticket_distribution_start_datetime = data.get('ticket_distribution_start_datetime')
    is_ticket_distribution_permitted = data.get('is_ticket_distribution_permitted', 'false').lower() == 'true'
    number_of_tickets = data.get('number_of_tickets')
    department = data.get('department')
    professor_name = data.get('professor_name')
    event_type = data.get('event_type')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']

    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.update_event(event_id, event_name, event_datetime, event_end_datetime, event_location, event_description, ticket_distribution_start_datetime, is_ticket_distribution_permitted, number_of_tickets, department, professor_name, event_type)

    if success:
        return '', 204
    else:
        return '', 403

@main.route('/remove_event/', methods=['POST'])
def remove_event():
    data = request.get_json()
    event_id = data.get('event_id')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.remove_event(event_id)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/publish_ticket', methods=['POST'])
def publish_ticket():
    data = request.get_json()
    owner_id = data.get('owner_id')
    event_id = data.get('event_id')
    ticket_count = int(data.get('ticket_count', 1))
    if ticket_count <= 0:
        return jsonify({'reason': 'invalid_count'}), 400
    handler = current_app.config['handler']
    success, result = handler.publish_tickets_bulk(owner_id, event_id, ticket_count)
    if success:
        return '', 204
    else:
        fail_reason = result
        if fail_reason == 'no_remaining':
            return jsonify({'reason': 'no_remaining'}), 403
        elif fail_reason == 'not_permitted':
            return jsonify({'reason': 'not_permitted'}), 403
        elif fail_reason == 'not_found':
            return jsonify({'reason': 'not_found'}), 404
        elif fail_reason == 'id_error':
            return jsonify({'reason': 'id_error'}), 500
        elif fail_reason == 'integrity_error':
            return jsonify({'reason': 'integrity_error'}), 500
        elif fail_reason == 'not_started':
            return jsonify({'reason': 'not_started'}), 403
        else:
            return jsonify({'reason': 'error'}), 500

@main.route('/get_tickets_list', methods=['GET'])
def get_tickets_list():
    owner_id = request.args.get('user_id')
    handler = current_app.config['handler']
    tickets = handler.get_tickets_list_as_json(owner_id)
    if tickets is None:
        return '', 403
    return jsonify({'tickets': tickets}), 200

@main.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
    data = request.get_json()
    event_id = data.get('event_id')
    owner_id = data.get('owner_id')
    ticket_id = data.get('ticket_id')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if owner_id != operator_id and not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.cancel_ticket(event_id, owner_id, ticket_id)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/get_user_data_list', methods=['GET'])
def get_user_data_list():
    handler = current_app.config['handler']
    operator_id = request.cookies.get('user_id')
    if not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    users = handler.get_user_data_list_as_json()
    if users is None:
        return '', 403
    return jsonify({'users': users}), 200

@main.route('/reset_user', methods=['POST'])
def reset_user():
    user_id = request.form['user_id']
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.reset_user(user_id)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/change_permission_level', methods=['POST'])
def change_permission_level():
    user_id = request.form['user_id']
    is_admin_str = request.form.get('is_admin')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    if is_admin_str is None:
        return '', 400
    is_admin = is_admin_str.lower() == 'true'
    success = handler.update_user_data(user_id, is_admin=is_admin)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.delete_user(user_id)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    handler = current_app.config['handler']
    if handler.login(user_id, old_password):
        success = handler.update_user_data(user_id, new_password, None, None)
        if success:
            return '', 204
        else:
            return '', 403

@main.route('/give_ticket', methods=['POST'])
def give_ticket():
    data = request.get_json()
    owner_id = data.get('owner_id')
    event_id = data.get('event_id')
    ticket_count = data.get('ticket_count')
    is_forced = data.get('is_forced')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = True
    for _ in range(int(ticket_count)):
        if not handler.publish_ticket(owner_id, event_id, is_forced):
            success = False
            break
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/use_ticket', methods=['POST'])
def use_ticket():
    data = request.get_json()
    event_id = data.get('event_id')
    ticket_id = data.get('ticket_id')
    password = data.get('password')
    handler = current_app.config['handler']
    success = handler.use_ticket(event_id, ticket_id, password)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/cancel_all_unused_tickets', methods=['POST'])
def cancel_all_unused_tickets():
    data = request.get_json()
    event_id = data.get('event_id')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    success = handler.cancel_all_unused_tickets(event_id)
    if success:
        return '', 204
    else:
        return '', 403

@main.route('/create_accout_by_srvacc', methods=['POST'])
def create_accout_by_srvacc():
    data = request.get_json()
    user_id = data.get('user_id')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id != 'SrvAcc':
        return '', 401
    handler.create_user(user_id)
    return '', 204

@main.route('/get_event_checkin_password', methods=['POST'])
def get_event_checkin_password():
    data = request.get_json()
    event_id = data.get('event_id')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    password = handler.get_event_checkin_password(event_id)
    if password is None:
        return '', 403
    return jsonify({'password': password}), 200

@main.route('/publish_paper_ticket', methods=['POST'])
def publish_paper_ticket():
    data = request.get_json()
    event_id = data.get('event_id')
    is_forced = data.get('is_forced')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    ticket_data = handler.publish_paper_ticket(event_id, is_forced)
    if not ticket_data:
        return '', 403
    return jsonify({'ticket_data': ticket_data}), 200

@main.route('/create_account_by_email_address', methods=['POST'])
def create_account_by_email_address():
    data = request.get_json()
    email_address = data.get('email_address')
    handler = current_app.config['handler']
    user_id = handler.create_user(email_address=email_address)
    if user_id:
        default_password = user_id
        handler.send_email(user_id, f'ユーザー登録完了のお知らせ', f'お世話になります。理工展連絡会総務局実研講 事前予約窓口です。\n\n事前整理券配布システムへのユーザー登録が完了いたしました。\n\nもしこのメールに心当たりがない場合はお手数ですがその旨をご返信にてお知らせください。\n\n下記ユーザー名、初期パスワードでログインを行ってください。\n\nユーザーID: {user_id}\n初期パスワード: {default_password}\n\n＊必ずCookie及びJavaScriptを有効にしてご利用ください。また、プライベートモード等をご利用の場合正常に動作しない可能性があります。')
        return '', 204
    else:
        return '', 403

@main.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    user_id = data.get('user_id')
    subject = data.get('subject')
    body = data.get('body')
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    if handler.send_email(user_id, subject, body):
        return '', 204
    else:
        return '', 403
    
@main.route('/change_email_address', methods=['POST'])
def change_email_address():
    data = request.get_json()
    user_id = data.get('user_id')
    new_email_address = data.get('new_email_address')
    password = data.get('password')
    handler = current_app.config['handler']
    if handler.login(user_id, password):
        success = handler.update_user_data(user_id, None, None, new_email_address)
        if success:
            handler.send_email(user_id, f'【理工展】メールアドレス変更のお知らせ', f'お世話になっております。理工展連絡会総務局実研講 事前予約窓口です。\n\nメールアドレスの変更が完了いたしました。\n\nもしこのメールに心当たりがない場合はお手数ですがその旨をご返信にてお知らせください。')
            return '', 204
        else:
            return '', 403
    else:
        return '', 403
    
@main.route('/send_bulk_email', methods=['POST'])
def send_bulk_email():
    data = request.get_json()
    subject = data.get('subject')
    body = data.get('body')
    is_to_all_users = data.get('is_to_all_users', False)
    is_to_event_nonholders = data.get('is_to_event_nonholders', False)
    event_id = data.get('event_id', None)
    operator_id = request.cookies.get('user_id')
    handler = current_app.config['handler']
    if operator_id == 'SrvAcc' or not handler.is_admin(operator_id):
        return '', 401
    if handler.get_session_token(operator_id) != request.cookies.get('session_token'):
        return '', 401
    if not subject or not body:
        return '', 400
    success = handler.send_bulk_email(subject, body, is_to_all_users, event_id, is_to_event_nonholders)
    if success:
        return '', 204
    else:
        return '', 403


@main.route('/delete_own_account', methods=['POST'])
def delete_own_account():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    handler = current_app.config['handler']
    if not handler.login(user_id, password):
        return '', 401
    if handler.delete_user(user_id):
        return '', 204
    else:
        return '', 500
