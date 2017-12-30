'''
TODO:

add css for tasks priority instead of code generation
also we do not have to generate htmls, js is providing ncie wrappers for creating html nodes
dat db
sorting implementation
add timestamps
'''
from __future__ import print_function
from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
from pprint import pprint
import random
import codecs
from htmlgen import TaskHtml

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tasker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app)
thread = None

db = SQLAlchemy(app)


#models
class DBTasks(db.Model):
    '''    'id': #unique
        {timestamp:'date',
        task:'information about task',
        severity:'1-6', #where 1 is the highest, defines color of background
        ####solver:'username',  NOT NEEDED ANYMORE, as claimer == solver
        claimer:'username',
        requestor:'username',
        state:'done,ongoing,todo'
    '''
    __tablename__ = 'tasks'
    ID = db.Column(db.String(8), primary_key=True)
    timestamp = db.Column(db.String(20))
    content = db.Column(db.String(2000))
    severity = db.Column(db.Integer)
    claimer = db.Column(db.String(20))
    requestor = db.Column(db.String(20))
    state = db.Column(db.String(20))

    def __unicode__(self):
        return self.ID

def init_db():
    db.create_all(app=app)


def add_task(task):
    '''
    adding task to db
    '''
    task_id = codecs.encode(os.urandom(4), 'hex').decode("utf-8")
    if 'state' not in task:
        task['state'] = 'todo'
    if 'severity' not in task:
        task['severity'] = 5
    else:
        task['severity'] = int(task['severity'])
    if 'requestor' not in task:
        task['requestor'] = 'Automata'
    pprint(task)
    db.session.add(DBTasks(ID=task_id, timestamp='timestamp',
        content=str(task['content']), severity=task['severity'],
        claimer='', requestor=task['requestor'], state=task['state']))
    db.session.commit()
    emit_task(task_id, task)

def emit_all_tasks():
    for task in DBTasks.query.all():
        emit_task(task.ID, task.__dict__, one_user=True)

def modify_task(task_id, new_data):
    '''
    new_data = {key:newvalue}
    '''
    DBTasks.query.filter_by(ID=task_id).update(new_data)
    db.session.commit()
    task = DBTasks.query.filter_by(ID=task_id).first()
    if not task:
        print('for : {}'.format(task_id))
    else:
        emit_task(task_id, task.__dict__, modify=True)



def emit_task(id, task, one_user=False, modify=False):
    '''
    TODO:
        add timestamp
        ugly html generation, maybe templates would be better?
        look at the top of the document
    '''
    node_code = TaskHtml(task, id).generate()
    if one_user:
        if modify:
            emit.emit('replace_task',  {'id':id, 'new_code':node_code})
        else:
            emit('add_task', {'new_code':node_code})
    else:
        if modify:
            socketio.emit('replace_task',  {'id':id, 'new_code':node_code}, namespace='/test')
        else:
            socketio.emit('add_task', {'new_code':node_code}, namespace='/test')

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('add_task', namespace='/task')
def add_task_socketio(task):
    add_task({'content': task['content'], 'severity':task['severity']})

@socketio.on('add_task_manual', namespace='/test')
def add_task_manual(msg):
    print('called!')
    add_task({'content': msg['task_description'], 'requestor': msg['user'], 'severity': msg['priority']})

@socketio.on('username', namespace='/test')
def login(message):
    emit('log', {'data': 'New user: '+ message['username']}, broadcast=True)
    emit_all_tasks()

@socketio.on('take_task', namespace='/test')
def propagate_take_task(message):
    modify_task(message['id'], {'claimer':message['user'], 'state':'ongoing'})

@socketio.on('end_task', namespace='/test')
def propagate_end_task(message):
    modify_task(message['id'], {'state':'done'})

if __name__ == '__main__':
    db.create_all()
    socketio.run(app, port=80, host="0.0.0.0")

