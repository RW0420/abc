from threading import Thread
from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO, emit
import time
from main import fb_login, login_test, waiting, select_seat

app = Flask(__name__)
socketio = SocketIO(app)
date_v = None
seat_v = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login_test") # type: ignore
def LGT():
    login_test_st = login_test()
    if login_test_st == True:
        return jsonify(success=True)
    elif login_test_st == False:
        return jsonify(success=False)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    print(email, password)
    login_st = fb_login(email, password)
    if login_st == True:
        return jsonify(success=True)
    elif login_st == False:
        return jsonify(success=False)
    return jsonify(success=False)

@app.route("/date", methods=['POST'])
def date():
    global date_v
    data = request.get_json()
    date_v = data.get("date")
    print(date_v)
    return jsonify(success=True)

@app.route("/seat", methods=['POST'])
def seat():
    global seat_v
    data = request.get_json()
    seat_v = data.get("seat")
    print(seat_v)
    return jsonify(success=True)

@app.route("/all_status")
def all_status():
    data = {
        "login": login_test(),
        "date": date_v,
        "seat": seat_v,
    }
    return jsonify(data)

@app.route("/start")
def start():
    thread = Thread(target=link_task)
    thread.start()
    return jsonify(success=True)

def link_task():
    global waiting_v
    while True:
        push_log(f"正在獲取連結:{date_v}")
        waiting_v = waiting(date_v)
        if waiting_v is not None:
            push_log(f"獲取設定的日期連結:{waiting_v}")
            thread = Thread(target=select_seat, args=(waiting_v,seat_v,))
            thread.start()
            break
        else:
            push_log(f"未找到符合條件的連結，繼續等待...")  # 更新此處的日誌訊息
            time.sleep(0.3)

def push_log(log):
    socketio.emit('new_log', {'log': log})

def Take_Your_Ticket(img):
    socketio.emit('Take_Your_Ticket', {'b64': img})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0")