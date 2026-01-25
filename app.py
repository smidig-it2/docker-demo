import os
import sqlite3
from pathlib import Path

import flask
import requests

import dash


class Database:
    def __init__(self, app: flask.Flask):
        db_path_env = os.getenv("DB_PATH")
        if db_path_env:
            self.db_path = Path(db_path_env)
        else:
            self.db_path = Path(__file__).resolve().parent.joinpath('db', 'flask.sqlite')

        # sørg for at mappen finnes
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.app = app
        self.init_db()
        self.app.teardown_appcontext(self.close_db)


    def init_db(self):
        with self.app.app_context():
            db = self.get_db()
            self.create_table(db)
            # Legg til eksempeldata bare hvis tabellen er tom
            antall = db.execute('SELECT COUNT(*) FROM personer').fetchone()[0]
            if antall == 0:
                db.executemany(
                    'INSERT INTO personer (navn, alder, bosted) VALUES (?, ?, ?)',
                    [
                        ('Bjarne Bogen', 48, 'Bergen'),
                        ('Ella Evensen', 20, 'Elverum'),
                        ('Hilde Hov', 22, 'Hamar')
                    ]
                )
            db.commit()

    def get_db(self):
        if 'db' not in flask.g:
            flask.g.db = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            flask.g.db.row_factory = sqlite3.Row
        return flask.g.db

    def create_table(self, db):
        db.cursor().executescript("""
        CREATE TABLE IF NOT EXISTS personer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            navn TEXT,
            alder INTEGER,
            bosted TEXT
        );
        """)

    def close_db(self, exception):
        db = flask.g.pop('db', None)
        if db is not None:
            db.close()


class Server:
    def __init__(self):
        self.flask = flask.Flask(__name__)
        self.database = Database(self.flask)
        self.setup_routes()

    def setup_routes(self):
        @self.flask.route("/personer", methods=['GET'])
        def les_personer():
            try:
                db = self.database.get_db()
                personer = db.execute('SELECT * FROM personer').fetchall()
                return flask.jsonify([dict(person) for person in personer])
            except Exception as e:
                return flask.jsonify({"status": type(e).__name__,
                                      "melding": str(e)}), 500

        @self.flask.route("/personer", methods=['POST'])
        def legg_til_person():
            try:
                db = self.database.get_db()
                new_person = flask.request.json
                db.execute(
                    'INSERT INTO personer (navn, alder, bosted) VALUES (?, ?, ?)',
                    (new_person['navn'], new_person['alder'],
                     new_person['bosted'])
                )
                db.commit()
                return flask.jsonify({"status": "OK",
                                      "melding": "Personen ble lagt til"}), 201
            except Exception as e:
                return flask.jsonify({"status": type(e).__name__,
                                      "melding": str(e)}), 500

        @self.flask.route("/personer", methods=['PUT'])
        def rediger_person():
            try:
                db = self.database.get_db()
                redigert_person = flask.request.json
                id = redigert_person['id']
                rowcount = db.execute(
                    'UPDATE personer SET navn = ?, \
                        alder = ?, bosted = ? WHERE id = ?',
                    (redigert_person['navn'], redigert_person['alder'],
                        redigert_person['bosted'], id)
                ).rowcount
                db.commit()
                if rowcount == 0:
                    return flask.jsonify({"status": "Feil",
                                          "melding": "Personen ble ikke funnet"}), 404
                return flask.jsonify({"status": "OK",
                                      "melding": "Personen ble oppdatert"}), 200
            except Exception as e:
                return flask.jsonify({"status": type(e).__name__,
                                      "melding": str(e)}), 500

        @self.flask.route("/personer/<int:id>", methods=['DELETE'])
        def slett_person(id):
            try:
                db = self.database.get_db()
                rowcount = db.execute(
                    'DELETE FROM personer WHERE id = ?', (id,)).rowcount
                db.commit()
                if rowcount == 0:
                    return flask.jsonify({"status": "Feil",
                                          "melding": "Personen ble ikke funnet"}), 404
                return flask.jsonify({"status": "OK",
                                      "melding": "Personen ble slettet"}), 200
            except Exception as e:
                return flask.jsonify({"status": type(e).__name__,
                                      "melding": str(e)}), 500


class DashApp:
    def __init__(self, flask_app: flask.Flask) -> None:
        self.app = dash.Dash(__name__, server=flask_app,
                             routes_pathname_prefix='/')
        self.app.title = 'Flask Dash SQLite demo'
        self.data_server = []
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self) -> None:
        self.app.layout = dash.html.Div([
            dash.dcc.Interval(id='interval_id',
                              interval=3000, disabled=False),
            dash.dcc.Tabs(id='tabs', value='home', children=[
                dash.dcc.Tab(label='Hjem', value='home', children=[
                    dash.dcc.Markdown('''
                        # Hilsen Smidig IT-2
                        Her kan vi skrive vanlig markdown med  
                        **fet** og *kursiv* tekst, osv.
                        ''', style={'textAlign': 'center'})
                ]),
                dash.dcc.Tab(label='Persondata', value='persondata', children=[
                    dash.dcc.Markdown(
                        id='info_id', children='Henter data fra server...'),
                    dash.html.Button(
                        'Legg til rad', id='ny_rad_id', n_clicks=0),
                    dash.html.Button('Lagre endringer',
                                     id='lagre_id', n_clicks=0),
                    dash.dash_table.DataTable(
                        id='tabell_id',
                        columns=[
                            {'name': 'Id', 'id': 'id',
                             'type': 'numeric', 'editable': False},
                            {'name': 'Navn', 'id': 'navn',
                             'type': 'text', },
                            {'name': 'Alder', 'id': 'alder',
                             'type': 'numeric'},
                            {'name': 'Bosted', 'id': 'bosted',
                             'type': 'text'}
                        ],
                        editable=True,
                        sort_action='native',
                        sort_by=[{'column_id': 'id', 'direction': 'asc'}],
                        row_deletable=True,
                        style_header={'fontWeight': 'bold',
                                      'textAlign': 'center'}
                    ),
                ])
            ]),
            dash.html.Div(id='output')
        ])

    def setup_callbacks(self) -> None:
        @self.app.callback(
            dash.Output('tabell_id', 'data'),
            dash.Output('interval_id', 'disabled'),
            dash.Output('info_id', 'children'),
            dash.Input('interval_id', 'n_intervals'),
            dash.Input('ny_rad_id', 'n_clicks'),
            dash.Input('lagre_id', 'n_clicks'),
            dash.Input('tabell_id', 'data'),
        )
        def kombinert_callback(n_intervals: int, ny_rad_n_clicks: int,
                               lagre_n_clicks: int, data: list) -> tuple:
            ctx = dash.callback_context
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if trigger_id == 'interval_id':
                data_hentet = hent_data()
                if data_hentet is None:
                    return dash.no_update, dash.no_update,  "Kunne ikke hente data. Prøver igjen om 3 sekunder"
                else:
                    self.data_server = data_hentet
                    return data_hentet, True, "Hentet data."
            elif trigger_id == 'ny_rad_id':
                data.append({"id": None, "navn": None,
                            "alder": None, "bosted": None})
                return data, dash.no_update, "Ulagrede endringer"
            elif trigger_id == 'tabell_id':
                if data != self.data_server:
                    return dash.no_update, dash.no_update, \
                        "Ulagrede endringer"
                else:
                    return dash.no_update, dash.no_update, \
                        "Tabelldata lik serverdata"
            elif trigger_id == 'lagre_id':
                if data == self.data_server:
                    return dash.no_update, dash.no_update, \
                        "Ingen endringer å lagre"
                else:
                    data_server_oppslag = {
                        item['id']: item
                        for item in self.data_server}

                    personer_nye = [item for item in data if not item['id']]
                    feil = legg_til_personer(personer_nye)
                    if feil:
                        return dash.no_update, dash.no_update, feil

                    personer_endret = [item for item in data
                                       if item['id'] in data_server_oppslag
                                       and item != data_server_oppslag[item['id']]]
                    feil = endre_personer(personer_endret)
                    if feil:
                        return dash.no_update, dash.no_update, feil

                    # Lag sett med ID-er til slettede personer
                    # Ikke ta med nye rader uten ID
                    data_id_sett = {d['id']
                                    for d in data if d['id'] is not None}
                    data_server_id_sett = {item['id']
                                           for item in self.data_server}
                    id_sett_slettet = data_server_id_sett - data_id_sett
                    feil = slett_personer(id_sett_slettet)
                    if feil:
                        return dash.no_update, dash.no_update, feil

                    data = hent_data()
                    if data is None:
                        return dash.no_update, False, \
                            "Kunne ikke hente data. Prøver igjen om 3 sekunder"
                    else:
                        self.data_server = data
                        return data, True, "Endringer lagret"

            return dash.no_update, dash.no_update, dash.no_update

        def hent_data() -> list | None:
            try:
                response = requests.get('http://127.0.0.1:5000/personer')
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                return None

        def legg_til_personer(personer: list) -> str | None:
            if not personer:
                return None
            try:
                for person in personer:
                    response = requests.post(
                        'http://127.0.0.1:5000/personer', json=person)
                    response.raise_for_status()
                return None
            except requests.exceptions.RequestException as e:
                return "Feil ved å legge til personer."

        def endre_personer(personer: list) -> str | None:
            if not personer:
                return None
            try:
                for person in personer:
                    response = requests.put(
                        f'http://127.0.0.1:5000/personer', json=person)
                    response.raise_for_status()
                return None
            except requests.exceptions.RequestException as e:
                return "Feil ved oppdatering av personer."

        def slett_personer(id_sett: set) -> str | None:
            if not id_sett:
                return None
            try:
                for id in id_sett:
                    response = requests.delete(
                        f'http://127.0.0.1:5000/personer/{id}')
                    response.raise_for_status()
                return None
            except requests.exceptions.RequestException as e:
                return "Feil ved sletting av personer."


if __name__ == "__main__":
    server = Server()
    dash_app = DashApp(server.flask)
    server.flask.run(host="0.0.0.0", port=5000, debug=False, threaded=True)


# Smidig IT-2 © TIP AS, 2026
