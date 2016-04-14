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
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

#PATH = os.path.dirname('/home/pi/MusicBlocks/')
# PATH = os.path.dirname(__file__)

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

db = SQLAlchemy(app)
from models import *

Bootstrap(app)


# def get_db():
#     db = getattr(g, '_database', None)
#     if db is None:
#         db = g._database = sqlite3.connect(flask.config['PATH'] + '/MusicBlocks.db',
#                                            detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None)
#         db.row_factory = sqlite3.Row
#     return db


# @app.teardown_appcontext
# def close_connection(exception):
#     db = getattr(g, '_database', None)
#     if db is not None:
#         db.close()


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
    # cursor = get_db().cursor()
    # blocks = cursor.execute('SELECT * FROM block_table').fetchall()
    block_numbers = db.session.query(Block.number).order_by(Block.number).all()
    form.block_number.choices = [(block.number, block.number) for block in block_numbers]
    if form.validate_on_submit():
        song_filename = secure_filename(form.file.data.filename)
        song = db.session.query(Song).filter_by(file=song_filename).one_or_none()
        if song is None:
            song = Song(title=form.song_title.data, file=song_filename)
            form.file.data.save(flask.config['PATH'] + '/Music/%s' % song_filename)
            db.session.add(song)
        else:
            song.title = form.song_title.data
        block = db.session.query(Block).filter_by(number=form.block_number.data).one()
        block.song = song
        db.session.commit()
    # cursor.execute('''SELECT block_number, song_table.song_name, count FROM song_table
    #                   LEFT OUTER JOIN (SELECT song_name AS sn, count(*) AS count FROM play_history_table
    #                   GROUP BY song_name) ON song_name = sn''')
    # blocks = cursor.fetchall()
    counts =  db.session.query(PlayHistory.song_title, func.count('*').\
        label('play_count')).\
        group_by(PlayHistory.song_title).subquery()
    blocks = db.session.query(Block.number, Song.title, counts.c.play_count).join(Song).outerjoin(counts, Song.title == counts.c.song_title).order_by(Block.number).all()
    # cursor.execute('''SELECT time_played, play_history_table.song_name, block_number FROM play_history_table
    #                   LEFT OUTER JOIN song_table ON song_table.song_name=play_history_table.song_name
    #                   ORDER BY time_played DESC''')
    history = db.session.query(PlayHistory).order_by(PlayHistory.time_played.desc()).limit(10)
    return render_template('index.html', cs_form=form, blocks=blocks, history=history)


@app.route('/advanced', methods=['GET', 'POST'])
def advanced():
    form = AdvancedForm()
    #cursor = get_db().cursor()
    #blocks = cursor.execute('SELECT * FROM block_table').fetchall()
    block_numbers = db.session.query(Block.number).order_by(Block.number).all()
    form.block_number.choices = [(block.number, block.number) for block in block_numbers]
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
            #cursor.execute('DELETE FROM block_table WHERE block_number=?', str(form.block_number.data))
            block = db.session.query(Block).filter_by(number=form.block_number.data).one()
            db.session.delete(block)
            db.session.commit()
            form.block_number.choices.remove((form.block_number.data, form.block_number.data))
            flash('Block %i deleted' % form.block_number.data, 'success')
    return render_template('advanced.html', form=form)

app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
