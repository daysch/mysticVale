from flask import Flask, flash, redirect, jsonify, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import time
import game
from helpers import apology, jinja_debug


# Configure application
app = Flask(__name__)
gamer = game.Game()
app.config['SECRET_KEY'] = "Your_secret_string"
app.jinja_env.filters["debug"] = jinja_debug

@app.route("/",methods=["GET","POST"])
def index():
    """User welcome screen"""
    if 'id' in session:
        if gamer.in_progress:
            return redirect('/play')
        else:
            return redirect('/wait')
    if 'name' in session:
        return redirect('/wait')

    if request.method == "GET":
        return render_template('index.html')

    # verify name
    name = request.form.get('name')
    if not name:
        return apology('Please provide player name')
    if name in [player.name for player in gamer.players.values()]:
        return apology('Player name already in use')

    session['name'] = name

    # send to waiting room
    return redirect('/wait')

@app.route("/wait",methods=["GET","POST"])
def wait():
    if 'name' not in session:
        return redirect('/')
    if request.method == "POST":
        # add player
        if 'id' not in session or session['id'] not in gamer.players:
            session['id'] = gamer.add_player(session['name'])

    # remove player if necessary
    if 'id' in session and (session['id'] not in gamer.players or gamer.players[session['id']].name != session['name']):
        del session['id']

    # if player is in game and game has started, redirect to game
    elif 'id' in session and gamer.in_progress:
        return redirect('/play')

    # update known player count
    session['num_players'] = len(gamer.players)
    return render_template('wait.html',players=gamer.get_players(),leaders=gamer.using_leaders)

@app.route("/play")
def play():
    if 'id' not in session or 'name' not in session:
        return redirect('/wait')
    if session['id'] not in gamer.players or gamer.players[session['id']].name != session['name']:
        return redirect('/wait')
    if not gamer.in_progress:
        gamer.new_game()
    if gamer.needs_leader(session['id']):
        (leaders, opposites) = gamer.leader_options(session['id'])
        return render_template('leaders.html',leaders=leaders,opposites=opposites)

    session['known_turn_status'] = gamer.get_turn_status()
    return render_template('game.html', state=gamer.get_state(session['id']))

@app.route("/waiting")
def waiting():
    if gamer.in_progress and 'id' in session:
        return jsonify(True)
    if 'num_players' in session:
        return jsonify(session['num_players'] != len(gamer.players))
    else:
        return jsonify(False)

@app.route("/buy")
def buy():
    # Get username
    if "valeID" in request.args:
        return jsonify(gamer.add_vale(session['id'],request.args.get('valeID')))
    return jsonify(None)

@app.route("/move")
def move():
    return jsonify(gamer.move(request.args.get('item'),request.args.get('source'),request.args.get('destination'),session['id'],request.args.get('source_card')))

@app.route("/action")
def action():
    if request.args.get('action') == 'push':
        return jsonify(gamer.play_on_deck(session['id']))
    elif request.args.get('action') == 'flip':
        return jsonify(gamer.flip(session['id']))
    elif request.args.get('action') == 'end_turn':
        return jsonify(gamer.end_turn(session['id']))
    elif request.args.get('action') == 'flip_token':
        return jsonify(gamer.flip_token(session['id']))
    elif request.args.get('action') == 'score_points':
        return jsonify(gamer.score_points(session['id'],1))
    elif request.args.get('action') == 'lose_points':
        return jsonify(gamer.score_points(session['id'], -1))
    elif request.args.get('action') == 'add_bank':
        return jsonify(gamer.add_points(1))
    elif request.args.get('action') == 'sub_bank':
        return jsonify(gamer.add_points(-1))
    elif request.args.get('action') == 'shuffle':
        return jsonify(gamer.shuffle(session['id']))
    elif request.args.get('action') == 'discard_vale':
        return jsonify(gamer.discard_vale(session['id'],request.args.get('vale'),request.args.get('source')))
    elif request.args.get('action') == 'set_color':
        return jsonify(gamer.set_color(session['id'], request.args.get('color')))
    elif request.args.get('action') == 'set_leaders':
        return jsonify(gamer.set_leaders(request.args.get('using_leaders')))
    elif request.args.get('action') == 'set_leader':
        return jsonify(gamer.set_leader(session['id'],request.args.get('leader')))
    elif request.args.get('action') == 'flip_leader':
        return jsonify(gamer.flip_leader(session['id']))
    elif request.args.get('action') == 'discard_field':
        return jsonify(gamer.discard_field(session['id']))


@app.route('/update')
def update():
    # no change
    turn_status = gamer.get_turn_status()
    if session['known_turn_status'] == turn_status or (turn_status[0] == session['id'] and turn_status[1] != 0):
        return jsonify(None)

    session['known_turn_status'] = turn_status
    player = gamer.get_state(session['id'])['players_turn']
    # current player is now requester
    if not player:
        return jsonify({'status':session['known_turn_status'],'field':None})
    return jsonify({'status':session['known_turn_status'],'field':render_template('field.html',player=player)})

@app.route("/debug",methods=["GET","POST"])
def debug():
    if request.method == 'POST':
        exec(request.form.get("exec"))
    return render_template('debug.html')
