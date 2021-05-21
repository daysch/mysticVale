from flask import Flask, flash, redirect, jsonify, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
import time
import game
import pickle
from helpers import apology, jinja_debug, render_field
from pympler import asizeof


# Configure application
app = Flask(__name__)
gamer = game.Game()
app.config['SECRET_KEY'] = "Your_secret_string"
app.jinja_env.filters["debug"] = jinja_debug
app.jinja_env.filters["render_field"] = render_field

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

    reload_update_known()
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

@app.route("/load_game",methods=["POST"])
def load_game():
    global gamer
    if not gamer.players:
        with open('saved_game', 'rb') as infile:
            gamer = pickle.load(infile)
            print('loaded')
    for player in gamer.players.values():
        if player.name == session['name']:
            session['id'] = player.id
            return redirect('/play')

@app.route("/move")
def move():
    data = gamer.move(request.args.get('item'),request.args.get('source'),request.args.get('destination'),session['id'],request.args.get('source_card'))
    if data:
        return jsonify(data)
    else:
        state = gamer.get_state(session['id'])
        return jsonify({'full_html':render_template('game.html', state=state),
                    'deck-display':render_template('deck.html', state=state),
                    'discard':render_template('discard.html', state=state),
                    'field':render_template('own_field.html', state=state),
                    'vales-owned':render_template('own_vales.html', state=state),
                    'purgatory':render_template('purgatory.html', state=state),
                    'num_vales':len(state['vales']),
                    'num_discard':len(state['discard'])
                   })

@app.route("/action")
def action():
    if request.args.get('action') == 'push':
        gamer.play_on_deck(session['id'])
    elif request.args.get('action') == 'flip':
        gamer.flip(session['id'])
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
        gamer.shuffle(session['id'])
    elif request.args.get('action') == 'discard_vale':
        gamer.discard_vale(session['id'],request.args.get('vale'),request.args.get('source'))
    elif request.args.get('action') == 'set_color':
        return jsonify(gamer.set_color(session['id'], request.args.get('color')))
    elif request.args.get('action') == 'set_leaders':
        return jsonify(gamer.set_leaders(request.args.get('using_leaders')))
    elif request.args.get('action') == 'set_leader':
        return jsonify(gamer.set_leader(session['id'],request.args.get('leader')))
    elif request.args.get('action') == 'flip_leader':
        return jsonify(gamer.flip_leader(session['id']))
    elif request.args.get('action') == 'discard_field':
        gamer.discard_field(session['id'])
    elif request.args.get('action') == 'undo':
         gamer.restore_state(session['id'],int(request.args.get('number')))
    else:
        raise Exception('Invalid Action')

    state = gamer.get_state(session['id'])
    return jsonify({'full_html':render_template('game.html', state=state),
                    'deck-display':render_template('deck.html', state=state),
                    'discard':render_template('discard.html', state=state),
                    'field':render_template('own_field.html', state=state),
                    'vales-owned':render_template('own_vales.html', state=state),
                    'purgatory':render_template('purgatory.html', state=state),
                    'num_vales':len(state['vales']),
                    'num_discard':len(state['discard'])
                   })


@app.route('/update')
def update():
    requested_player = str(request.args.get('player'))
    players_turn = gamer.get_players_turn()
    turn_status = gamer.get_turn_status(requested_player)

    # no change
    if session['known_players_turn'] == players_turn and session['known_turn_statuses'][requested_player] == turn_status:
        return jsonify({'your_turn':None,'full_html':None,'requested_field':None,'turn_name':None})

    # now it's current player's turn
    if session['known_players_turn'] != players_turn and players_turn == session['id']:
        reload_update_known()
        return jsonify({'full_html':render_template('game.html', state=gamer.get_state(session['id'])),
                        'your_turn':True,'requested_field':None, 'turn_name':None})

    # new player's turn, update all
    if session['known_players_turn'] != players_turn:
        reload_update_known()

        # get field data
        state=gamer.get_state(session['id'])
        turn_name = state['players_turn']['name']
        return jsonify({'full_html':render_template('game.html', state=state),
                        'your_turn':False,'requested_field':None,'turn_name':turn_name})

    ## just one player to update
    # player has hit undo, so we need to update the whole field
    elif session['known_turn_statuses'][requested_player] > turn_status:
        reload_update_known()

        # get field data
        state=gamer.get_state(session['id'])
        return jsonify({'full_html':render_template('game.html', state=state),
                        'your_turn':False,'requested_field':None,'turn_name':None})

    # update known information
    player = gamer.get_other_state(requested_player)
    known_turn_statuses = session['known_turn_statuses']
    known_turn_statuses.update({requested_player:turn_status})
    session['known_turn_statuses'] = known_turn_statuses
    state = gamer.get_state(session['id'])

    # prepare return value
    rv = jsonify({'requested_field':render_template('field.html',player=player),
                  'advancements':render_template('advancements.html',state=state) if session['known_adv_state'] != state['adv_state'] else None,
                  'vales-available':render_template('vales.html',state=state) if session['known_vale_state'] != state['vale_state'] else None,
                  'turn_field':None,'full_html':None,'reload':False})
    session['known_adv_state'] = state['adv_state']
    session['known_vale_state'] = state['vale_state']
    return rv

@app.route("/debug",methods=["GET","POST"])
def debug():
    if request.method == 'POST':
        exec(request.form.get("exec"))
    return render_template('debug.html')

def reload_update_known():
    session['known_turn_statuses'] = gamer.get_turn_statuses()
    session['known_players_turn'] = gamer.get_players_turn()
    session['known_adv_state'] = gamer.get_adv_state()
    session['known_vale_state'] = gamer.get_vale_state()