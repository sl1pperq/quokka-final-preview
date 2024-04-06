from flask import *
import random
import uuid
import time
import markdown
from sender import send_email_message
from gpt import create_prompt
from system import run_code
import sys
from io import StringIO
from diploma import create_diploma
import qrcode
import datetime
from words import *

app = Flask(__name__)
app.secret_key = "QuokkaQuiz"
quiz = []
user = []
social = []
shop = []
orders = []
bank = {}
groups = []

try:
    with open('json/quiz.json', 'r') as file:
        quiz = json.loads(file.read())
    with open('json/user.json', 'r') as file:
        user = json.loads(file.read())
    with open('json/social.json', 'r') as file:
        social = json.loads(file.read())
    with open('json/shop.json', 'r') as file:
        shop = json.loads(file.read())
    with open('json/orders.json', 'r') as file:
        orders = json.loads(file.read())
    with open('json/bank.json', 'r') as file:
        bank = json.loads(file.read())
    with open('json/groups.json', 'r') as file:
        groups = json.loads(file.read())
except:
    pass


def save_data():
    with open('json/quiz.json', 'w') as file:
        file.write(json.dumps(quiz, ensure_ascii=False))
    with open('json/user.json', 'w') as file:
        file.write(json.dumps(user, ensure_ascii=False))
    with open('json/social.json', 'w') as file:
        file.write(json.dumps(social, ensure_ascii=False))
    with open('json/shop.json', 'w') as file:
        file.write(json.dumps(shop, ensure_ascii=False))
    with open('json/orders.json', 'w') as file:
        file.write(json.dumps(orders, ensure_ascii=False))
    with open('json/bank.json', 'w') as file:
        file.write(json.dumps(bank, ensure_ascii=False))
    with open('json/groups.json', 'w') as file:
        file.write(json.dumps(groups, ensure_ascii=False))


@app.route('/')
def main_page():
    if session.get("auth", False) == False:
        auth_token = str(uuid.uuid4())
        hour = datetime.datetime.now().hour
        hello = say_hello_main(hour)
        return render_template('main.html', auth=0, token=auth_token, hello=hello)
    else:
        hour = datetime.datetime.now().hour
        hello = say_hello_main(hour)
        return render_template('main.html', auth=1, hello=hello)


@app.template_filter('shuffle')
def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


@app.route('/constructor')
def main_menu_constructor():
    if session.get("auth", False) == False:
        return render_template('main.html', auth=0)
    else:
        if detect_bank_user(session['auth']) == True:
            user_bank = bank[session['auth']]
        else:
            bank[session['auth']] = []
            user_bank = bank[session['auth']]
        u = get_user_limits(session['auth'])
        return render_template('menu.html', auth=session['auth'], quiz=quiz, user=u, groups=groups, bank=user_bank)


@app.route('/constructor/<id>')
def constructor(id):
    q = find_quiz(id)
    return render_template('create.html', quiz=q, id=id)

@app.route('/teacher/login')
def teacher_login():
    return render_template('enter.html')

@app.route('/constructor/create/<type>')
def create_constructor(type):
    id = str(random.randint(100000, 999999))
    quiz.append({
        'id': id,
        'type': type,
        'status': "Close",
        'plan': None,
        'author': session['auth'],
        'text': None,
        'title': None,
        'protect': False,
        'result': [],
        'test': [],
        'settings': {
            'special': None,
            'notify': None,
            'hide_res': None,
            'diploma': None
        }
    })
    add_used_quiz(session['auth'])
    save_data()
    return redirect(f'/constructor/{id}')


@app.route('/save/main/<id>', methods=['POST'])
def save_main_info(id):
    title = request.form.get('title')
    text = request.form.get('text')

    special = request.form.get('special')
    notify = request.form.get('notify')
    hide_res = request.form.get('hide_res')
    diploma = request.form.get('diploma')

    set_main_info(id, title, text)
    set_save(id, special, notify, hide_res, diploma)
    return redirect(f'/constructor/{id}')


@app.route('/create/<type>/<id>')
def create_new_quiz(type, id):
    task_id = str(random.randint(100000, 999999))
    add_new_task(id, type, task_id)
    return redirect(f'/constructor/{id}?focusquiz#test{task_id}')


@app.route('/delete/quiz/<id>/<quiz_id>')
def del_quiz(id, quiz_id):
    delete_quiz(id, quiz_id)
    return redirect(f'/constructor/{id}?focusquiz')


@app.route('/save/quiz/<id>/<type>/<test_id>', methods=['POST'])
def save_quiz_info(id, type, test_id):
    text = request.form.get('text')
    img_url = request.form.get('image')
    html_text = markdown.markdown(text)
    save_quiz(id, test_id, html_text, img_url)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/add/answer/<id>/<type>/<quiz_id>')
def add_answer_quiz(id, type, quiz_id):
    add_answer(id, type, quiz_id)
    return redirect(f'/constructor/{id}?focusquiz#test{quiz_id}')


@app.route('/save/answer/<id>/<test_id>/<answer_id>', methods=['POST'])
def save_answer_to_quiz(id, test_id, answer_id):
    answer = request.form.get('answer')
    save_answer(id, test_id, answer_id, answer)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/del/answer/<id>/<test_id>/<answer_id>')
def del_quiz_answer(id, test_id, answer_id):
    del_answer(id, test_id, answer_id)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/set/answer/status/<id>/<test_id>/<a_id>/<status>')
def change_answer_status(id, test_id, a_id, status):
    if status == "True" or status == True:
        status = False
    else:
        status = True
    set_answer_status(id, test_id, a_id, status)
    return redirect(f'/constructor/{id}?focusquiz?focusquiz#test{test_id}')


@app.route('/student/quiz/<id>')
def get_student_solve(id):
    q = find_quiz(id)
    soc_user = ''
    if session.get('social', False) == False:
        pass
    else:
        soc_user = find_social(session['social'])
    pre_text = random_prequiz()
    sklon = true_word_form(len(q['test']))
    return render_template('solve.html', start=True, id=id, quiz=q, sklon=sklon, soc=soc_user, pre_text=pre_text)


@app.route('/student/quiz/<id>', methods=['POST'])
def post_student_solve(id):
    q = find_quiz(id)
    name = request.form.get('name')
    unum = str(uuid.uuid4())
    session['student'] = unum
    session['num'] = 1
    session['quiz'] = id
    session['after'] = 0
    if session.get('social', False) == False:
        pass
    else:
        soc_user = find_social(session['social'])
        if soc_user['premium'] != False:
            session['premium'] = 1
    if q['type'] == 'bee':
        add_empty_bee_result(id, unum, name)
    else:
        add_empty_result(id, unum, name)
    add_start_time(id, unum, time.time())
    return redirect(f'/student/quiz')


@app.route('/student/quiz')
def student_quiz_num():
    id = session['quiz']
    num = int(session['num'])
    q = find_quiz(id)
    if int(num) > len(q['test']):
        result = find_quiz_result(id, session['student'])
        add_finish_time(id, session['student'], time.time())
        find_total_time(id, session['student'])
        q = find_quiz(session['quiz'])
        after_ask = session['after']
        stud = session['student']
        del session['student']
        del session['num']
        del session['quiz']
        del session['after']
        proc_result = round(int(result['score']) / len(q['test'] * 100))
        if q['settings']['notify'] == "on":
            send_email_message(session['auth'], f'Ученик №{stud} прошел ваш квиз! Подробности на сайте!',
                               'Ученик прошел квиз')

        soc_mail = ""
        socuser = ''
        if session.get('social', False) == False:
            pass
        else:
            soc_mail = session['social']
            find_and_done_social_task(session['social'], id, result['score'])

        points = int(result['score'])

        if session.get('premium', False) == False:
            pass
        else:
            points = points * 2
            add_limit_to_user(q['author'], 1)
            print("points", points)

        soc_add_points(soc_mail, result['score'], id, len(q['test']), q['title'])

        socuser = find_social(soc_mail)

        return render_template('solve.html', start="Final", id=id, result=result, len=len(q['test']), quiz=q,
                               after_ask=after_ask, proc_result=proc_result, stud=stud, soc_mail=soc_mail,
                               points=points, socuser=socuser)
    else:
        color = None
        if q['type'] == 'bee':
            color = find_user_bee_color(id, session['student'])
        premium = 0
        if session.get('premium', False) == False:
            pass
        else:
            premium = 1
        print(premium)
        return render_template('solve.html', quiz=q, num=num, start=False, id=id, color=color, premium=premium)


@app.route('/social/quiz', methods=['POST'])
def social_quiz():
    mail = request.form.get('mail')
    id = request.form.get('id')
    points = request.form.get('points')
    all_points = request.form.get('all_points')
    title = request.form.get('title')
    if check_social(mail) == True:
        soc_add_points(mail, points, id, all_points, title)
        return redirect(f'/student/quiz/{id}')
    else:
        return redirect(f'/student/quiz/{id}')


@app.route('/student/quiz/answer', methods=['POST'])
def student_quiz_num_answer():
    id = session['quiz']
    num = session['num']
    answer = request.form.get('ans')
    q = find_quiz(id)
    if q['status'] == "Close":
        result = find_quiz_result(id, session['student'])
        add_finish_time(id, session['student'], time.time())
        find_total_time(id, session['student'])
        del session['student']
        del session['num']
        del session['quiz']
        del session['after']
        return render_template('solve.html', start="QuizClose", result=result, len=len(q['test']), id=id)
    print(answer)
    n = int(num) + 1
    session['num'] = n
    if find_answer_type(id, num) == "after_check":
        session['after'] += 1
        add_after_result(id, session['student'], answer)
        return redirect(f'/student/quiz')
    elif find_answer_type(id, num) == "python_code":
        i_data, o_data, length = get_python_io_data(id, num)
        print(i_data, o_data, length)
        counter = 0
        i_data, o_data, length = get_python_io_data(id, num)
        for i in range(0, length):
            input_data = i_data[i]
            output_data = o_data[i]
            sys.stdin = StringIO(input_data)
            old_stdout = sys.stdout
            redirected_output = sys.stdout = StringIO()
            try:
                exec(answer)
            except Exception as e:
                print(e)
            sys.stdout = old_stdout
            result = redirected_output.getvalue()
            print(str(result.strip()), str(output_data.strip()))
            if str(result.strip()) == str(output_data.strip()):
                counter += 1
        if counter == length:
            add_true_result(id, session['student'], "Правильный код")
        elif counter > 0 and counter < length:
            add_mixed_result(id, session['student'], f'Python: {counter} / {length}')
        else:
            add_false_result(id, session['student'], "Неправильный код")
        return redirect(f'/student/quiz')
    elif find_answer_type(id, num) == "cross":
        result = check_answer_cross(id, num, answer)
        if result == 'Correct answer':
            add_true_result(id, session['student'], answer)
        else:
            add_false_result(id, session['student'], answer)
        return redirect(f'/student/quiz')
    else:
        if session.get('premium', False) == False:
            pass
        else:
            if session['premium'] == 1:
                if answer == 'ПОДСКАЗКА':
                    add_true_result(id, session['student'], answer)
                    session['premium'] = 0
                    return redirect(f'/student/quiz')
                else:
                    pass
            else:
                pass
        result = check_answer(id, num, answer)
        if result == 'Correct answer':
            add_true_result(id, session['student'], answer)
        else:
            add_false_result(id, session['student'], answer)
        return redirect(f'/student/quiz')


@app.route('/find/quiz', methods=['POST'])
def find_quiz_post():
    id = request.form.get('num')
    if bool_find_quiz(id) == True:
        return redirect(f'/student/quiz/{id}')
    else:
        return render_template('main.html', error="Такой квиз не найден")


@app.route('/login/check', methods=['POST'])
def login_check_post():
    mail = request.form.get('email')
    password = request.form.get('password')
    u = find_user(mail, password)
    if u == "OK":
        session['auth'] = mail
        return redirect('/constructor')
    elif u == "Incorrect password":
        return render_template('main.html', error="Пароль неверный, повторите попытку")
    elif u == "User not found":
        create_user(mail, password)
        session['auth'] = mail
        return redirect('/constructor')


@app.route('/whoid/login')
def whoid_login():
    result = request.args.get('status')
    mail = request.args.get('mail')
    if result == "Success":
        u = find_user_mail(mail)
        if u == True:
            session['auth'] = mail
            return redirect('/constructor')
        elif u == False:
            create_user(mail, 'password')
            session['auth'] = mail
            return redirect('/constructor')
    else:
        return redirect('/')


@app.route('/constructor/delete/<id>')
def del_quiz_app(id):
    del_quiz_def(id)
    del_used_quiz(session['auth'])
    return redirect('/constructor?focusquiz')


@app.route('/value/user/answer/<id>/<ans>/<val>')
def value_user_answer(id, ans, val):
    change_user_answer(id, ans, val)
    mail = find_remember_user_mail(id, ans)
    if mail != "None" or mail is not None:
        send_email_message(mail, f'Учитель проверил ваш ответ, у вас {val} правильных заданий!', 'Задание проверено')
    return redirect(f'/dashboard/answers/{id}')


@app.route('/remember/mail/<id>/<stud>', methods=['POST'])
def send_after_mail(id, stud):
    mail = request.form.get('mail')
    remember_user_mail(id, stud, mail)
    return render_template('solve.html', id=id, start="SuccessMail")


@app.route('/add/gpt/answer/<id>/<task_id>')
def add_gpt_answer(id, task_id):
    add_system_answer(id, task_id)
    return redirect(f'/constructor/{id}?focusquiz#test{task_id}')


@app.route('/add/gpt/plan/<id>')
def add_gpt_plan(id):
    create_gpt_plan(id)
    return redirect(f'/constructor/{id}')


@app.route('/dashboard/answers/<id>')
def quiz_show_answers(id):
    q = find_quiz(id)
    return render_template('answers.html', quiz=q, id=id)


@app.route('/show/board/mode/<id>/<num>')
def show_board_mode(id, num):
    q = find_quiz(id)
    all_info = show_list_test(id)[int(num) - 1]
    return render_template('board.html', test=all_info, num=int(num), id=id, quiz=q, mode='classic')


@app.route('/show/bee/mode/<id>')
def show_board_bee_mode(id):
    q = find_quiz(id)
    return render_template('board.html', id=id, quiz=q, mode="bee")


@app.route('/bee/board/update/<id>')
def bee_borad_update(id):
    q = find_quiz(id)
    update_bee_status(id)
    return redirect(f'/show/bee/mode/{id}')


@app.route('/add/checkpoint/<id>/<test_id>')
def add_checkpoint(id, test_id):
    add_new_check_point(id, test_id)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/save/checkpoint/<id>/<test_id>/<check_id>', methods=['POST'])
def save_checkpoint(id, test_id, check_id):
    code_input = request.form.get("input")
    code_output = request.form.get("output")
    saving_checkpoint_info(id, test_id, check_id, code_input, code_output)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/del/checkpoint/<id>/<test_id>/<check_id>')
def del_checkpoint(id, test_id, check_id):
    delete_quiz_checkpoint(id, test_id, check_id)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/quiz/open/<id>')
def open_quiz(id):
    func_open_quiz(id)
    return redirect(f'/constructor/{id}')


@app.route('/quiz/close/<id>')
def close_quiz(id):
    func_close_quiz(id)
    return redirect(f'/constructor/{id}')


@app.route('/set/cross/answer/<id>/<test_id>', methods=['POST'])
def set_cross_answer(id, test_id):
    answer = request.form.get('answer')
    set_cross_quiz_answer(id, test_id, answer)
    return redirect(f'/constructor/{id}?focusquiz#test{test_id}')


@app.route('/api/find/quiz/<id>')
def api_find_quiz(id):
    return jsonify(find_quiz(id))


@app.route('/api/quiz/text/<id>')
def api_quiz_text(id):
    texts, answers = for_api_find_text_answer(id)
    print(texts)
    return jsonify(texts)


@app.route('/api/quiz/answer/<id>')
def api_quiz_answer(id):
    texts, answers = for_api_find_text_answer(id)
    print(answers)
    return jsonify(answers)


@app.route('/api/answer/quiz/<id>/<score>/<name>')
def api_answer_quiz(id, score, name):
    add_telegram_result(id, score, name)
    return jsonify({"status": "OK"})


@app.route('/pay/noti/<kolvo>', methods=['POST', 'GET'])
def payment_notify(kolvo):
    mail = request.args.get('customerEmail')
    kolvo = int(kolvo)
    add_limit_to_user(mail, kolvo)
    return jsonify({"status": "Pay"})

@app.route('/pay/protect', methods=['POST', 'GET'])
def payment_notify_protect():
    print(request.data)
    return jsonify({"status": "OK"})


@app.route('/pay/after')
def payment_after():
    return render_template('pay.html')


@app.route('/save/settings/<id>', methods=['POST'])
def post_settings(id):
    return redirect(f'/constructor/{id}')


@app.route('/diploma/create', methods=['POST'])
def diploma_create():
    user_name = request.form.get('user_name')
    quiz_name = request.form.get('quiz_name')
    create_diploma(user_name, quiz_name)
    return send_file('static/user_diploma.png')


@app.route('/qr/create/<id>')
def qr_create(id):
    with open('static/qr.png', 'w') as file:
        file = qrcode.make(f'https://pro.quokkaquiz.ru/student/quiz/{id}')
        file.save('./static/qr.png')
        return send_file('static/qr.png')


@app.route('/logout')
def logout():
    del session['auth']
    return redirect('/')


@app.route('/social/connect')
def soc_connect():
    return render_template('social.html', start=True)


@app.route('/social/reg', methods=['POST'])
def soc_reg():
    name = request.form.get('name')
    mail = request.form.get('mail')
    if check_social(mail) == False:
        id = str(random.randint(100000, 999999))
        social.append({
            'mail': mail,
            'balance': 0,
            'name': name,
            'id': id,
            'solved': 0,
            'premium': False,
            'history': [],
            'quizes': [],
            'tasks': []
        })
        save_data()
        session['social'] = mail
        send_email_message(
            mail,
            f'Добро пожаловать в QuokkaConnect! Вы сможете получать призы, просто решая квизы. Чтобы все результаты засчитывались - не забывайте после прохождения вводить индивидуальный номер - <h1>{id}</h1>',
            'Добро пожаловать!'
        )
        return redirect('/social/my')
    else:
        return redirect('/social/my')


@app.route('/social/my')
def social_my():
    if session.get('social', False) == False:
        return render_template('social.html', start=False, auth=0)
    else:
        u = find_social(session['social'])
        now_time = time.time()
        if u['premium'] == False:
            pass
        else:
            if u['premium'] <= now_time:
                u['premium'] = False
                save_data()
        return render_template('social.html', start=False, auth=1, user=u, shop=shop, orders=orders)


@app.route('/social/log', methods=['POST'])
def social_log():
    mail = request.form.get('mail')
    code = str(random.randint(100000, 999999))
    session['code'] = code
    session['mail'] = mail
    if check_social(mail) == True:
        send_email_message(
            mail,
            f'Вход в аккаунт QuokkaConnect. Для входа введите ваш код, он будет действовать в течении нескольких минут - <h1>{code}</h1>',
            'Подтверждение входа QuokkaConnect'
        )
        return render_template('social.html', start=False, auth=0, code=mail)
    else:
        return redirect('/social/my')


@app.route('/social/code', methods=['POST'])
def social_code():
    code = request.form.get('code')
    print(code, session['code'])
    if str(code) == str(session['code']):
        session['social'] = session['mail']
        del session['mail']
        del session['code']
        return redirect('/social/my')
    else:
        return render_template('social.html', start=False, auth=0, code=session['mail'])


@app.route('/shop/buy/<id>', methods=['POST'])
def shop_buy(id):
    item = find_item(id)
    soc_user = find_social(session['social'])
    if soc_user['balance'] >= item['price']:
        soc_user['balance'] -= item['price']
        save_data()
        name = request.form.get('name')
        phone = request.form.get('phone')
        clas = request.form.get('class')
        delivery = request.form.get('delivery')
        order_id = str(random.randint(1000000, 9999999))
        data = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        new_order = {
            'id': order_id,
            'mail': soc_user['mail'],
            'phone': phone,
            'item_id': item['id'],
            'item_title': item['title'],
            'price': item['price'],
            'status': 'Принят',
            'title': item['title'],
            'date': data,
            'class': clas,
            'delivery': delivery,
            'name': name
        }
        orders.append(new_order)
        save_data()
        send_email_message(
            session['social'],
            f'Ваш заказ №{new_order["id"]} на сумму {new_order["price"]} QC успешно <b>оформлен</b><p>Вы получите уведомление, когда заказ будет готов к выдаче</p><i>По всем вопросам обращайтесь на почту help@quokkaquiz.ru</i>',
            'Заказ оформлен'
        )
        return render_template('social.html', start=False, auth=2, order=new_order)
    else:
        return redirect('/social/my')


@app.route('/shop/console')
def shop_console():
    return render_template('admin.html', orders=orders)


@app.route('/shop/order/<id>/<stat>')
def shop_set_stat(id, stat):
    new_st = get_new_status(stat)
    o = find_order(id)
    set_new_order_status(id, new_st)
    return redirect('/shop/console')


@app.route('/one')
def show_one():
    soc_u = find_social(session['social'])
    return render_template('one.html', soc_u=soc_u)


@app.route('/one/new', methods=['POST'])
def one_create_sign():
    mail = request.form.get('mail')
    create_new_premium(mail)
    return render_template('one.html', soc_u=soc_u)


@app.route('/one/noti', methods=['POST', 'GET'])
def one_payment_notify():
    mail = request.args.get('customerEmail')
    # summa = int(request.args.get('productPrice'))
    create_new_premium(mail)
    return jsonify({"status": "Pay"})


@app.route('/list')
def quiz_list_show():
    return render_template('list.html', quiz=quiz)


@app.route('/bank')
def open_bank():
    if detect_bank_user(session['auth']) == True:
        user_bank = bank[session['auth']]
        return render_template('bank.html', bank=user_bank)
    else:
        bank[session['auth']] = []
        return redirect('/bank')


@app.route('/bank/add/<id>/<tid>')
def bank_add(id, tid):
    if detect_bank_user(session['auth']) == True:
        new_test = find_need_test(id, tid)
        bank[session['auth']].append(new_test)
        save_data()
        return redirect(f'/constructor/{id}?focusquiz#test{tid}')
    else:
        bank[session['auth']] = []
        return redirect(f'/bank/add/{id}/{tid}')


@app.route('/bank/import/<id>', methods=['POST'])
def post_bank_import(id):
    num = request.form.get('number')
    task = get_task_from_bank(num)
    if task == False:
        return redirect(f'/constructor/{id}')
    else:
        if from_bank_quiz_id_find(id, num) == False:
            add_task_to_quiz_bank(id, task)
            return redirect(f'/constructor/{id}?focusquiz#test{task["id"]}')
        else:
            return redirect(f'/constructor/{id}?focusquiz#test{num}')


@app.route('/bank/del/<id>')
def bank_del(id):
    delete_task_from_bank(id)
    return redirect('/constructor?focusbox')


@app.route('/quality/check/<id>/<tid>')
def check_quality(id, tid):
    gpt_check_test(id, tid)
    return redirect(f'/constructor/{id}?focusquiz#test{tid}')

@app.route('/group')
def group():
    return render_template('group.html', groups=groups, author=session['auth'], open=0)

@app.route('/group/<id>')
def group_open(id):
    g = find_group(id)
    return render_template('group.html', group=g, open=1)

@app.route('/group/create', methods=['POST'])
def group_create():
    title = request.form.get('title')
    groups.append({
        "id": str(random.randint(100000, 999999)),
        "title": title,
        "author": session['auth'],
        "students": [],
        "works": [],
        "messages": []
    })
    save_data()
    return redirect('/group')

@app.route('/group/<id>/new/student', methods=['POST'])
def group_add_user(id):
    number = request.form.get('number')
    if find_social_id(number) == True:
        u = find_social_user(number)
        add_new_group_user(id, u)
        return redirect(f'/group/{id}')
    else:
        return redirect(f'/group/{id}')

@app.route('/group/<id>/new/work', methods=['POST'])
def group_add_task(id):
    number = request.form.get('number')
    if find_if_quiz(number) == True:
        q = find_quiz(number)
        title = q['title']
        add_new_group_task(id, q)
        send_stud_new_task(id, title, number)
        return redirect(f'/group/{id}')
    else:
        return redirect(f'/group/{id}')

@app.route('/group/<group_id>/send/<quiz_id>/<user_id>/<result>')
def group_send_info(group_id, quiz_id, user_id, result):
    u = find_social_id_full(user_id)
    send_info_to_teacher(group_id, quiz_id, u, result)
    return redirect('/social/my')

@app.route('/support/send', methods=['POST'])
def support_send():
    text = request.form.get('text')
    worker = random_name_choice()
    send_email_message(session['auth'], f'Спасибо за обращение в службу поддержки, специалист все проверит и отправит вам ответ в течении одного рабочего дня!<p>С уважением, менеджер службы поддержки учителей {worker}!</p>', "Служба поддержки учителей КвоккаКвиз")
    send_email_message("hi@quokkaquiz.ru", f'Вопрос от учителя {session["auth"]}: <p>{text}</p>', 'Новый запрос в поддержку')
    return redirect('/constructor')

@app.route('/sales/send', methods=['POST'])
def sales_send():
    typi = request.form.get('type')
    kolvo = request.form.get('kolvo')
    text = request.form.get('text')
    worker = random_name_choice()
    send_email_message(session['auth'], f'Ваш запрос в отдел продаж успешно отправлен! В течении одного рабочего дня с вами свяжется специалист.<p>С уважением, сотрудник отдела продаж {worker}!</p>', "Отдел продаж КвоккаКвиз")
    send_email_message("hi@quokkaquiz.ru", f'Учитель {session["auth"]} отправил запрос:<br><br>- {typi}<br>- {kolvo}<br>- {text}', 'Запрос в отдел продаж')
    return redirect('/constructor')

@app.route('/support/student', methods=['POST'])
def support_student_send():
    text = request.form.get('text')
    mail = request.form.get('mail')
    worker = random_name_choice()
    send_email_message(mail, f'Спасибо за внимательность и обращение в службу поддержки, наш специалист все проверит и свяжется с вами в течении одного рабочего дня!<p>С уважением, специалист службы поддержки учеников {worker}!</p>', "Служба поддержки учеников КвоккаКвиз")
    send_email_message("hi@quokkaquiz.ru", f'Вопрос от ученика {mail}: <p>{text}</p>', 'Новый запрос в поддержку')
    return redirect('/')

@app.route('/cheating/detect')
def detect_devtools():
    return render_template('cheating.html')


def change_social_send_status(user_id, quiz_id):
    for s in social:
        if s['id'] == user_id:
            for t in s['tasks']:
                if t['id'] == quiz_id:
                    t['send'] = True
                    save_data()

def send_info_to_teacher(group_id, quiz_id, u, result):
    for g in groups:
        if g['id'] == group_id:
            for w in g['works']:
                if w['id'] == quiz_id:
                    w['users'].append({
                        'id': u['id'],
                        'name': u['name'],
                        'mail': u['mail'],
                        'result': result,
                    })
                    change_social_send_status(u['id'], quiz_id)
                    save_data()


def find_and_done_social_task(mail, qid, res):
    for s in social:
        if s['mail'] == mail:
            for t in s['tasks']:
                if t['id'] == qid:
                    t['done'] = res
                    save_data()


def send_stud_new_task(id, title, tid):
    for g in groups:
        if g['id'] == id:
            for s in g['students']:
                text = f'Ваш учитель в группе <b>{g["title"]}</b> задал задание - пройти квиз "{title}" с ID <b>{tid}</b><p>Команда КвоккаКвиза желает вам успеха!)</p>'
                send_email_message(s['mail'], text, f"Новое задание в группе {g['title']}")
                for u in social:
                    if u['mail'] == s['mail']:
                        u['tasks'].append({
                            "id": tid,
                            "gid": g['id'],
                            "title": title,
                            "from": g['title'],
                            "done": False,
                            "send": False
                        })
                        save_data()
                        break



def add_new_group_task(gid, q):
    for g in groups:
        if g['id'] == gid:
            g['works'].append({
                'id': q['id'],
                'title': q['title'],
                'users': []
            })
            save_data()

def find_if_quiz(id):
    for q in quiz:
        if q['id'] == id:
            return True
    return False

def add_new_group_user(gid, u):
    for g in groups:
        if g['id'] == gid:
            g['students'].append({
                'id': u['id'],
                'mail': u['mail'],
                'name': u['name']
            })
            save_data()

def find_social_id(id):
    for s in social:
        if s['id'] == id:
            return True
    return False

def find_social_id_full(id):
    for s in social:
        if s['id'] == id:
            return s

def find_social_user(id):
    for s in social:
        if s['id'] == id:
            return s

def find_group(id):
    for g in groups:
        if g['id'] == id:
            return g


def delete_task_from_bank(id):
    b = bank[session['auth']]
    for q in b:
        if q['id'] == id:
            bank[session['auth']].remove(q)
            save_data()


def for_api_find_text_answer(id):
    texts = []
    answers = []
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                texts.append(t['text'])
                answers.append(t['answer'])
            break
    return texts, answers


def gpt_check_test(id, task_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == task_id:
                    title = q['title']
                    text = t['text']
                    answer = create_prompt(
                        f'Проверь вопрос из квиза с названием "{title}" на качество составления и дай рекомендации. Вот текст вопроса: "{text}"'
                    )
                    answer = markdown.markdown(answer)
                    t['quality'] = answer
                    save_data()


def from_bank_quiz_id_find(id, num):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == num:
                    return True
            break
    return False


def add_task_to_quiz_bank(id, task):
    for q in quiz:
        if q['id'] == id:
            q['test'].append(task)
            save_data()


def get_task_from_bank(num):
    b = bank[session['auth']]
    for q in b:
        if q['id'] == num:
            return q
    return False


def find_need_test(id, quiz_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == quiz_id:
                    return t


def detect_bank_user(mail):
    for key, value in bank.items():
        if key == mail:
            return True
    return False


def create_new_premium(mail):
    for s in social:
        if s['mail'] == mail:
            now_time = time.time()
            sub_stop = now_time + 2592000
            s['premium'] = sub_stop
            save_data()


def set_new_order_status(id, stat):
    for o in orders:
        if o['id'] == id:
            if stat == "В сборке":
                o['status'] = stat
                send_email_message(
                    o['mail'],
                    f'Сейчас мы начали бережно собирать ваш заказ №{o["id"]} - в нем товар {o["item_title"]}.<p>Следующим этапом заказ передадут курьеру для передачи в пункт выдачи</p><i>По всем вопросам обращайтесь на почту help@quokkaquiz.ru</i>',
                    'Ваш заказ собирается'
                )
                save_data()
            elif stat == 'В пути':
                o['status'] = stat
                send_email_message(
                    o['mail'],
                    f'Курьер получил заказ №{o["id"]} и спешит к пункту выдачи по адресу {o["delivery"]}<p>Когда заказ будет доставлен - вам придет уведомление. Также вы можете просматривать информацию о заказах в QuokkaQuiz</p><i>По всем вопросам обращайтесь на почту help@quokkaquiz.ru</i>',
                    'Заказ передан курьеру'
                )
                save_data()
            elif stat == 'Готов':
                o['status'] = stat
                send_email_message(
                    o['mail'],
                    f'Вы можете получить заказ №{o["id"]} по адресу - {o["delivery"]}<p>При необходимости с вами свяжутся по телефону и уточнят детали получения. Также для получения назоваите код <b>{random.randint(1000, 9999)}</b></p><i>По всем вопросам обращайтесь на почту help@quokkaquiz.ru</i>',
                    'Заказ готов к выдаче'
                )
                save_data()
            elif stat == 'Выдан':
                o['status'] = stat
                send_email_message(
                    o['mail'],
                    f'Спасибо, что оформили заказ в QuokkaConncet!<p><i>По всем вопросам обращайтесь на почту help@quokkaquiz.ru</i></p>',
                    'Заказ выдан'
                )
                save_data()


def find_order(id):
    for o in orders:
        if o['id'] == id:
            return o


def get_new_status(stat):
    stat = int(stat)
    if stat == 1:
        return "Принят"
    elif stat == 2:
        return "В сборке"
    elif stat == 3:
        return "В пути"
    elif stat == 4:
        return "Готов"
    elif stat == 5:
        return "Выдан"


def find_item(id):
    for i in shop:
        if i['id'] == id:
            return i


def soc_add_points(mail, points, id, all_points, title):
    for s in social:
        if s['mail'] == mail:
            s['balance'] += int(points)
            s['solved'] += 1
            s['quizes'].append({
                'id': id,
                'points': points,
                'all_points': all_points,
                'title': title
            })
            save_data()


def find_social(mail):
    for s in social:
        if s['mail'] == mail:
            return s
    return ''


def check_social(mail):
    for s in social:
        if s['mail'] == mail:
            return True
    return False


def set_save(id, special, notify, hide_res, diploma):
    for q in quiz:
        if q['id'] == id:
            set = q['settings']
            set['special'] = special
            set['notify'] = notify
            set['hide_res'] = hide_res
            set['diploma'] = diploma
            save_data()


def add_used_quiz(mail):
    for q in user:
        if q['mail'] == mail:
            q['used'] += 1
            save_data()


def del_used_quiz(mail):
    for q in user:
        if q['mail'] == mail:
            q['used'] -= 1
            save_data()


def add_limit_to_user(mail, summa):
    for u in user:
        if u['mail'] == mail:
            u['limit'] += summa
            save_data()


def set_cross_quiz_answer(id, test_id, answer):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    t['answer'] = answer
                    save_data()


def func_open_quiz(id):
    for q in quiz:
        if q['id'] == id:
            q['status'] = "Open"
            save_data()


def func_close_quiz(id):
    for q in quiz:
        if q['id'] == id:
            q['status'] = "Close"
            save_data()


def get_python_io_data(id, num):
    input_data = []
    output_data = []
    for q in quiz:
        if q['id'] == id:
            for t in range(len(q['test'])):
                if (t + 1) == num:
                    for c in range(len(q['test'][t]['checkpoints'])):
                        input_data.append(q['test'][t]['checkpoints'][c]['input'])
                        output_data.append(q['test'][t]['checkpoints'][c]['output'])
                    length = len(q['test'][t]['checkpoints'])
                    return input_data, output_data, length


def add_new_check_point(id, test_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    if 'checkpoints' in t:
                        pass
                    else:
                        t['checkpoints'] = []
                        save_data()
                    t['checkpoints'].append({
                        "id": str(uuid.uuid4()),
                        'input': "",
                        'output': ""
                    })
                    save_data()


def saving_checkpoint_info(id, test_id, point_id, code_input, output):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    for c in t['checkpoints']:
                        if c['id'] == point_id:
                            c['input'] = code_input
                            c['output'] = output
                            save_data()


def show_list_test(id):
    test_list = []
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                test_list.append(t)
    return test_list


def add_system_answer(id, task_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == task_id:
                    answer = create_prompt(
                        f'Напиши свой ответ на тему: {t["text"]}. Используй разметку Markdown, но не упоминай это в тексте')
                    answer = markdown.markdown(answer)
                    t['system'] = answer
                    save_data()


def create_gpt_plan(id):
    for q in quiz:
        if q['id'] == id:
            answer = create_prompt(
                f'Создай примерный план квиза по названию "{q["title"]} и описанию "{q["text"]}". Используй разметку Markdown, но не упоминай это в тексте')
            answer = markdown.markdown(answer)
            q['plan'] = answer
            save_data()


def remember_user_mail(id, ans_id, mail):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == ans_id:
                    r['mail'] = mail
                    save_data()


def find_remember_user_mail(id, ans_id):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == ans_id:
                    return r['mail']


def change_user_answer(id, ans_id, val):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == ans_id:
                    r['score'] += int(val)
                for a in r['answers']:
                    if a['is_true'] == "Wait":
                        a['is_true'] = "Checked"
                save_data()


def del_quiz_def(id):
    for q in quiz:
        if q['id'] == id:
            quiz.remove(q)
            save_data()


def delete_quiz_checkpoint(id, t_id, c_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == t_id:
                    for c in t['checkpoints']:
                        if c['id'] == c_id:
                            t['checkpoints'].remove(c)
                            save_data()


def create_user(mail, password):
    user.append({
        'mail': mail,
        'password': password,
        'used': 0,
        'limit': 10,
    })
    save_data()


def get_user_limits(mail):
    for u in user:
        if u['mail'] == mail:
            return u


def find_user(mail, password):
    for u in user:
        if u['mail'] == mail:
            if u['password'] == password:
                return "OK"
            else:
                return "Incorrect password"
    return "User not found"


def find_user_mail(mail):
    for u in user:
        if u['mail'] == mail:
            return True
    return False


def bool_find_quiz(id):
    for q in quiz:
        if q['id'] == id:
            return True
    return False


def bool_find_status(id):
    for q in quiz:
        if q['id'] == id:
            if q['status'] == "Close":
                return False
            else:
                return True


def find_quiz_result(id, uid):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == uid:
                    return r


def add_empty_result(id, uid, name):
    for q in quiz:
        if q['id'] == id:
            q['result'].append({
                "id": uid,
                "score": 0,
                "name": name,
                "answers": [],
                "start": None,
                "finish": None,
                "mail": None,
                "total": "Еще не пройдено"
            })
            save_data()


def add_empty_bee_result(id, uid, name):
    for q in quiz:
        if q['id'] == id:
            q['result'].append({
                "id": uid,
                'color': random.choice(colors),
                "score": 0,
                'active': True,
                "name": name,
                "answers": [],
                "start": None,
                "finish": None,
                "mail": None,
                "total": "Еще не пройдено"
            })
            save_data()


def find_user_bee_color(id, uid):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == uid:
                    return r['color']


def update_bee_status(id):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                r['active'] = False
                save_data()


def add_telegram_result(id, score, name):
    for q in quiz:
        if q['id'] == id:
            q['result'].append({
                "id": str(uuid.uuid4()),
                "score": score,
                "name": name,
                "answers": [
                    {
                        "answer": "Пройдено в Telegram",
                        "is_true": "Checked"
                    }
                ],
                "start": None,
                "finish": None,
                "mail": None,
                "total": "Пройдено"
            })
            save_data()


def find_total_time(id, res_id):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    total_sec = r['finish'] - r['start']
                    minutes = round(total_sec / 60)
                    seconds = round(total_sec % 60)
                    r['total'] = f'{minutes}:{seconds}'
                    save_data()


def add_start_time(id, res_id, time):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['start'] = time
                    save_data()


def add_finish_time(id, res_id, time):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['finish'] = time
                    save_data()


def add_false_result(id, res_id, answer):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['answers'].append({
                        "answer": answer,
                        "is_true": False
                    })
                    save_data()


def add_after_result(id, res_id, answer):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['answers'].append({
                        "answer": answer,
                        "is_true": "Wait"
                    })
                    save_data()


def add_true_result(id, res_id, answer):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['score'] += 1
                    r['answers'].append({
                        "answer": answer,
                        "is_true": True
                    })
                    save_data()


def add_mixed_result(id, res_id, answer):
    for q in quiz:
        if q['id'] == id:
            for r in q['result']:
                if r['id'] == res_id:
                    r['answers'].append({
                        "answer": answer,
                        "is_true": "Mixed"
                    })
                    save_data()


def check_answer(id, num, answer):
    for q in quiz:
        if q['id'] == id:
            for t in range(len(q['test'])):
                if (t + 1) == int(num):
                    for a in q['test'][t]['answer']:
                        print(a['answer'], answer)
                        if q['test'][t]['type'] == 'choice':
                            if a['answer'] == answer and a['true'] == True:
                                return "Correct answer"
                        else:
                            if a['answer'] == answer:
                                return "Correct answer"
    return "Answer not found"


def check_answer_cross(id, num, answer):
    for q in quiz:
        if q['id'] == id:
            for t in range(len(q['test'])):
                if (t + 1) == int(num):
                    if q['test'][t]['answer'] == answer:
                        return "Correct answer"
    return "Answer not found"


def find_answer_type(id, num):
    for q in quiz:
        if q['id'] == id:
            for t in range(len(q['test'])):
                if (t + 1) == int(num):
                    return q['test'][t]['type']


def find_quiz(id):
    for q in quiz:
        if q['id'] == id:
            return q


def set_main_info(id, title, text):
    for q in quiz:
        if q['id'] == id:
            q['title'] = title
            q['text'] = text
            save_data()


def add_new_task(id, type, task_id):
    for q in quiz:
        if q['id'] == id:
            if type == "cross":
                q['test'].append({
                    'id': task_id,
                    'image': None,
                    'quality': None,
                    'text': None,
                    'answer': "",
                    'type': type,
                    'system': None
                })
                save_data()
            else:
                q['test'].append({
                    'id': task_id,
                    'image': None,
                    'text': None,
                    'quality': None,
                    'answer': [],
                    'type': type,
                    'system': None
                })
                save_data()


def delete_quiz(id, quiz_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == quiz_id:
                    q['test'].remove(t)
                    save_data()


def save_quiz(id, quiz_id, text, img_url):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == quiz_id:
                    t['text'] = text
                    t['image'] = img_url
                    save_data()


def add_answer(id, type, quiz_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == quiz_id:
                    if type == 'choice':
                        t['answer'].append({
                            'id': str(random.randint(100000, 999999)),
                            'true': False,
                            'answer': None
                        })
                    else:
                        t['answer'].append({
                            'id': str(random.randint(100000, 999999)),
                            'answer': None
                        })
                    save_data()


def save_answer(id, test_id, answer_id, answer):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    for a in t['answer']:
                        if a['id'] == answer_id:
                            a['answer'] = answer
                            save_data()


def set_answer_status(id, test_id, answer_id, status):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    for a in t['answer']:
                        if a['id'] == answer_id:
                            a['true'] = status
                            save_data()


def del_answer(id, test_id, answer_id):
    for q in quiz:
        if q['id'] == id:
            for t in q['test']:
                if t['id'] == test_id:
                    for a in t['answer']:
                        if a['id'] == answer_id:
                            t['answer'].remove(a)
                            save_data()


def true_word_form(s):
    n1 = " вопросов"
    n2 = " вопрос"
    n3 = " вопроса"
    if s == 0:
        return str(s) + n1
    elif s % 100 >= 10 and s % 100 <= 20:
        return str(s) + n1
    elif s % 10 == 1:
        return str(s) + n2
    elif s % 10 >= 2 and s % 10 <= 4:
        return str(s) + n3
    else:
        return str(s) + n1


def say_hello_main(hour):
    if hour >= 6 and hour < 12:
        return 'Доброе утро! 🌝'
    elif hour >= 12 and hour < 18:
        return 'Добрый день! ☀️'
    elif hour >= 18 and hour < 22:
        return 'Добрый вечер! 🌚'
    elif hour >= 22 or hour < 6:
        return 'Доброй ночи! ✨'


colors = [
    '#CD5C5C',
    '#FFA07A',
    '#8B0000',
    '#FFC0CB',
    '#FF1493',
    '#DB7093',
    '#FF7F50',
    '#FF4500',
    '#FFA500',
    '#FFD700',
    '#EEE8AA',
    '#BDB76B',
    '#D8BFD8',
    '#EE82EE',
    '#BA55D3',
    '#8A2BE2',
    '#8B008B',
    '#4B0082',
    '#483D8B',
    '#7B68EE',
    '#ADFF2F',
    '#32CD32',
    '#00FF7F',
    '#2E8B57',
    '#9ACD32',
    '#808000',
    '#66CDAA',
    '#008B8B',
    '#AFEEEE',
    '#40E0D0',
    '#5F9EA0',
    '#B0C4DE',
    '#87CEEB',
    '#1E90FF',
    '#4169E1',
    '#000080',
    '#D2B48C',
    '#BC8F8F',
    '#FFDEAD',
    '##8B4513',
    '#800000'
]

app.run(port=5013)
