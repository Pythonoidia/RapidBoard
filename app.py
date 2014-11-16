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
from flask.ext.socketio import SocketIO, emit
from flask.ext.sqlalchemy import SQLAlchemy
import datetime
import os
from pprint import pprint
import random
from htmlgen import TaskHtml

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://{0}/tasker.db'.format(os.path.dirname(__file__))
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
    task_id = str(os.urandom(4).encode('hex'))
    if 'state' not in task:
        task['state'] = 'todo'
    if 'severity' not in task:
        task['severity'] = 5
    else:
        task['severity'] = int(task['severity'])
    if 'requestor' not in task:
        task['requestor'] = 'Automata'
    db.session.add(DBTasks(ID=task_id, timestamp='timestamp',
        content=str(task['content']), severity=task['severity'],
        claimer='', requestor=task['requestor'], state=task['state']))
    db.session.commit()

def emit_tasks():
    for task in DBTasks.query.all():
        print(task.__dict__)
        #node_code = TaskHtml(task.__dict__, task.ID).generate()
        Tasks().emit_task(task.ID, task.__dict__, one_user=True)

def modify_task(task_id, new_data):
    '''
    new_data = {key:newvalue}
    '''
    #DBTasks.query.filter(Clients.id == client_id_list).update({'status': status})
    DBTasks.query.filter_by(ID=task_id).update(new_data)
    task =  DBTasks.query.filter_by(ID=task_id).first()
    #task = db.session.query(DBTasks).filter(DBTasks.ID==task_id)
    pprint(task.__dict__)
    #task.update(new_data)
    #for key in new_data.keys():
    #    task.eval(key) = new_data[key]
    db.session.commit()
    #    self.emit_task(id, self.tasks[id], modify=True)



class Tasks(object):
    _tasks = {}
    '''
    We are Borg.
    ####Task:
    'id': #unique
    {timestamp:'date',
    content:'information about task',
    severity:'1-6', #where 1 is the highest, defines color of background
    ####solver:'username',  NOT NEEDED ANYMORE, as claimer == solver
    claimer:'username',
    requestor:'username',
    state:'done,ongoing,todo'

    }
    '''
    def __init__(self):
    #    tasksdb = TasksDB(request.form['title'], request.form['text'])
    #        db.session.add(todo)
        self.tasks = self._tasks
        self.id = str(os.urandom(4).encode('hex'))

    def add_task(self, task):
        '''
        adding task to class the storage and emiting it to clients
        '''
        if 'state' not in task:
            task['state'] = 'todo'
        if 'severity' not in task:
            task['severity'] = 5
        else:
            task['severity'] = int(task['severity'])
        if 'requestor' not in task:
            task['requestor'] = 'Automata'
        add_task(task)
        self.tasks[self.id] = task
        self.emit_task(self.id, task)
        return(self.id)

    def get_tasks(self):
        '''
        Returning all tasks which are stored in the class
        '''
        return(self.tasks)

    def modify_task(self, id, new_data):
        '''
        new_data = {key:newvalue}
        '''
        for key in new_data.keys():
            self.tasks[id][key] = new_data[key]
        self.emit_task(id, self.tasks[id], modify=True)

    @staticmethod
    def get_timestamp():
        return datetime.datetime.now()

    @staticmethod
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
            #emit('replace_task', {'id':id, 'new_code':end_code}, broadcast=True)

    def emit_all_tasks(self):
        for task in self._tasks:
            self.emit_task(task, self._tasks[task], one_user=True)


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('add_task', namespace='/task')
def add_task_socketio(task):
    Tasks().add_task({'content': task['content'], 'severity':task['severity']})

@socketio.on('add_task_manually', namespace='/test')
def add_task_manually(msg):
    Tasks().add_task({'content': msg['task_description'], 'requestor': msg['user'], 'severity': msg['priority']})

@socketio.on('username', namespace='/test')
def login(message):
    emit('log', {'data': 'New user: '+ message['username']}, broadcast=True)
    emit_tasks()
    #Tasks().emit_all_tasks()

@socketio.on('take_task', namespace='/test')
def propagate_take_task(message):
    modify_task(message['id'], {'claimer':message['user'], 'state':'ongoing'})
    #Tasks().modify_task(message['id'], {'claimer':message['user'], 'state':'ongoing'})

@socketio.on('end_task', namespace='/test')
def propagate_end_task(message):
    Tasks().modify_task(message['id'], {'state':'done'})

if __name__ == '__main__':
    db.create_all() 
    socketio.run(app, port=9095, host='localhost')
