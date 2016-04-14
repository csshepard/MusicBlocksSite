import sqlite3
import os
import subprocess
from flask import Flask, flash, render_template, g
from werkzeug.utils import secure_filename
from werkzeug.contrib.fixers import ProxyFix
from flask_bootstrap import Bootstrap
from flask_wtf import Form
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired


PATH = os.path.dirname('/home/pi/MusicBlocks/')
# PATH = os.path.dirname(__file__)

app = Flask(__name__)
app.config.from_object('config.Config')
Bootstrap(app)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(PATH + '/MusicBlocks.db',
                                           detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


class ChangeSong(Form):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['mp3'], 'Mp3s only')])
    block_number = SelectField('Block #', validators=[DataRequired()], coerce=int)
    song_title = StringField('Song Title', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AdvancedForm(Form):
    shutdown = SubmitField('Shutdown')
    reboot = SubmitField('Reboot')
    block_number = SelectField('Block #', coerce=int)
    delete = SubmitField('Delete Block')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ChangeSong()
    cursor = get_db().cursor()
    blocks = cursor.execute('SELECT * FROM block_table').fetchall()
    form.block_number.choices = [(block['block_number'], block['block_number']) for block in blocks]
    if form.validate_on_submit():
        song = secure_filename(form.file.data.filename)
        cursor.execute('SELECT file_name FROM song_table WHERE block_number=?', str(form.block_number.data))
        old_file = cursor.fetchone()['file_name']
        form.file.data.save(PATH + '/Music/%s' % song)
        cursor.execute('''UPDATE song_table SET song_name=?, file_name=?
                          WHERE block_number=?''', (form.song_title.data, song, str(form.block_number.data)))
        get_db().commit()
        try:
            if old_file != song:
                os.remove(PATH + '/Music/%s' % old_file)
        except OSError:
            pass
    cursor.execute('''SELECT block_number, song_table.song_name, count FROM song_table
                      LEFT OUTER JOIN (SELECT song_name AS sn, count(*) AS count FROM play_history_table
                      GROUP BY song_name) ON song_name = sn''')
    blocks = cursor.fetchall()
    cursor.execute('''SELECT time_played, play_history_table.song_name, block_number FROM play_history_table
                      LEFT OUTER JOIN song_table ON song_table.song_name=play_history_table.song_name
                      ORDER BY time_played DESC''')
    history = cursor.fetchmany(10)
    return render_template('index.html', cs_form=form, blocks=blocks, history=history)


@app.route('/advanced', methods=['GET', 'POST'])
def advanced():
    form = AdvancedForm()
    cursor = get_db().cursor()
    blocks = cursor.execute('SELECT * FROM block_table').fetchall()
    form.block_number.choices = [(block['block_number'], block['block_number']) for block in blocks]
    if form.validate_on_submit():
        if form.shutdown.data:
            subprocess.call(['shutdown -h now "System Shutdown from Web"'], shell=True)
            get_db().close()
            flash('System will shutdown in 1 minute', 'success')
        elif form.reboot.data:
            subprocess.call(['shutdown -r now "System Rebooted from Web"'], shell=True)
            get_db().close()
            flash('System will reboot in 1 minute', 'success')
        elif form.delete.data:
            query = cursor.execute('SELECT file_name FROM song_table WHERE block_number=?',
                                   str(form.block_number.data))
            song = query.fetchone()
            if song is not None:
                try:
                    os.remove(PATH+'/Music/%s' % song['file_name'])
                except OSError:
                    pass
                cursor.execute('DELETE FROM song_table WHERE block_number=?', str(form.block_number.data))
            cursor.execute('DELETE FROM block_table WHERE block_number=?', str(form.block_number.data))
            get_db().commit()
            form.block_number.choices.remove((form.block_number.data, form.block_number.data))
            flash('Block %i deleted' % form.block_number.data, 'success')
    return render_template('advanced.html', blocks=blocks, form=form)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
