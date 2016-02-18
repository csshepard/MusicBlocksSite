import sqlite3
import os
from flask import Flask, render_template, request, g
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


PATH = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
Bootstrap(app)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('/home/Chris/Projects/MusicBlocksSite/MusicBlocks.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


class ChangeSong(Form):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['mp3'],'Mp3s only')])
    block_number = SelectField('Block #', validators=[DataRequired()], coerce=int)
    song_title = StringField('Song Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ChangeSong()
    cursor = get_db().cursor()
    if form.validate_on_submit():
        song = secure_filename(form.file.data.filename)
        cursor.execute('SELECT file_name FROM song_table WHERE block_number=?', str(form.block_number.data))
        old_file = cursor.fetchone()['file_name']
        form.file.data.save('Music/' + song)
        cursor.execute('UPDATE song_table SET song_name=?, file_name=? WHERE block_number=?', (form.song_title.data,
                                                                                               song, str(form.block_number.data)))
        get_db().commit()
        try:
            os.remove(PATH+'/Music/%s' % old_file)
        except OSError:
            pass
    cursor.execute('SELECT block_number, song_table.song_name, count FROM song_table LEFT OUTER JOIN (SELECT song_name AS sn, count(*) AS count FROM play_history_table GROUP BY song_name) ON song_name = sn''')
    blocks = cursor.fetchall()
    cursor.execute('SELECT * FROM play_history_table')
    history = cursor.fetchmany(10)
    return render_template('index.html', cs_form=form, blocks=blocks, history=history)

if __name__ == '__main__':
    app.run()
