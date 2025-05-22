from flask import Flask, render_template, request, jsonify
from collections import defaultdict
from threading import Lock
import time


app = Flask(__name__)

pins = {}                  # строковый PIN -> judge_id (int)
scores = defaultdict(lambda: {'red': 0, 'blue': 0})
scores_lock = Lock()
active_judges = {}         # judge_id -> last_ping_time
active_lock = Lock()
PING_TIMEOUT = 10
fight_active = True
last_round_end_time = time.time()


scores = {
    1: {'red': 0, 'blue': 0},
    2: {'red': 0, 'blue': 0},
    3: {'red': 0, 'blue': 0},
    4: {'red': 0, 'blue': 0},


}


@app.route('/')
def index():
    return "\u0421\u0435\u0440\u0432\u0435\u0440 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442"


@app.route('/register_pin', methods=['POST'])
def register_pin():
    data = request.json
    pin = str(data['pin'])
    judge = int(data['judge'])
    pins[pin] = judge

    with active_lock:
        active_judges.pop(judge, None)

    scores[judge] = {'red': 0, 'blue': 0}
    print(f"✅ Зарегистрирован PIN: {pin} для судьи {judge}")

    return jsonify(status='ok', pin=pin)


@app.route('/judge/<pin>', methods=['GET', 'POST'])
def judge_panel(pin):
    pin = str(pin)
    if pin not in pins:
        return "Неверный PIN", 403

    # сразу получаем judge_id
    judge_id = pins[pin]

    # обновляем время «пинга» этого судьи
    with active_lock:
        active_judges[judge_id] = time.time()

    if request.method == 'POST':
        # разруливаем JSON или form-data в одном месте
        data = request.get_json(silent=True) or request.form
        color = data.get('color')
        points = int(data.get('points') or 0)

        with scores_lock:
            scores[judge_id][color] += points

        # возвращаем актуальные баллы именно этого судьи
        return jsonify(success=True, score=scores[judge_id])

    # GET — просто отрисовываем страницу
    return render_template(
        'judge_panel.html',
        pin=pin,
        judge=judge_id,
        score=scores[judge_id]
    )


@app.route('/score', methods=['POST'])
def submit_score():
    global fight_active, last_round_end_time
    if not fight_active:
        if time.time() - last_round_end_time > 2:
            return '', 204
    data = request.get_json()
    color = data['color']
    points = int(data['points'])
    pin = str(data['pin'])  # важно!

    if pin not in pins:
        return jsonify(success=False, error="Неверный PIN"), 403

    judge_id = pins[pin]
    scores[judge_id][color] += points

    print(f"Судья {judge_id} (PIN {pin}) дал {points} баллов за {color}")
    print(jsonify(scores))

    return jsonify(success=True, score=scores[judge_id])


@app.route('/scores', methods=['GET'])
def get_scores():
    with scores_lock:
        return jsonify(scores)


@app.route('/active_judges', methods=['GET'])
def get_active_judges():
    """Возвращаем список судей, которые «ping»-нулись в последние PING_TIMEOUT сек."""
    cutoff = time.time() - PING_TIMEOUT
    with active_lock:
        # удаляем просроченные
        for j, ts in list(active_judges.items()):
            if ts < cutoff:
                del active_judges[j]
        # возвращаем текущий список
        active = list(active_judges.keys())
    return jsonify(active_judges=active)


@app.route('/disconnect', methods=['POST'])
def judge_disconnect():
    data = request.get_json()
    pin = data.get('pin')
    if pin in pins:
        judge_id = pins[pin]
        with active_lock:
            active_judges.pop(judge_id, None)
    return '', 204


@app.route("/judge_ping", methods=["POST"])
def judge_ping():
    data = request.get_json()
    pin = data.get("pin")
    if pin in pins:
        judge_id = pins[pin]
        with active_lock:
            active_judges[judge_id] = time.time()
    return '', 204


# 2) ====== НОВЫЙ МАРШРУТ ДЛЯ СБРОСА ======
@app.route('/reset_scores', methods=['POST'])
def reset_scores():
    """Обнуляем баллы всех судей."""
    with scores_lock:
        for v in scores.values():
            v['red'] = v['blue'] = 0
    return '', 204
# =========================================


# 3) ====== ЭНД‑ПОЙНТ ДЛЯ ОДНОГО СУДЬИ ======
@app.route('/my_score/<pin>', methods=['GET'])
def my_score(pin):
    judge_id = pins.get(pin)
    if judge_id is None:
        return jsonify(error='неверный PIN'), 403
    with scores_lock:
        return jsonify(scores[judge_id])


@app.route('/set_fight_state', methods=['POST'])
def set_fight_state():
    global fight_active, last_round_end_time
    data = request.get_json()
    fight_active = data['fight_active']
    if not fight_active:
        last_round_end_time = time.time()
    return jsonify(success=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
