from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room
import datetime
from pprint import pprint

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None


def get_timestamp():
    return datetime.datetime.now()

class Tasks(object):
    _tasks = {}
    _id = []
    '''
    We are Borg.
    ####Task:
    'id': #unique
    {timestamp:'date',
    task:'information about task',
    severity:'1-9', #where 1 is the highest, defines color of background
    solver:'username',
    requestor:'username',
    state:'done,ongoing,todo'

    }
    '''
    def __init__(self):
        self.tasks = self._tasks
        if not self._id:
            self._id.append(0)
        self.id = self._id[0]
        self.id += 1
        self._id[0] = self.id
        print(self.id)
    def add_task(self, task):
        if 'state' not in task:
            task['state']='todo'
        self.tasks[self.id] = task

        socketio.emit('add_task',
                {'data': task['data'], 'id': self.id, 'state':task['state']}, namespace='/test')
        return(self.id)
    def get_tasks(self):
        return(self.tasks)
    def modify_task(self, id, new_data):
        '''
        new_data = {key:newvalue}
        '''
        id=int(id)
        for key in new_data.keys():
            self.tasks[id][key] = new_data[key]


def background_thread():
    """Example of how to send server generated events to clients."""
    """This thread should be an queue consumer"""
    """Consuming instances put into queue bar multiple other watchers"""
    while True:
        time.sleep(2)
        print('emit!')
        line='Errytime the same!'
        id = Tasks().add_task({'data': line, 
            'timestamp':get_timestamp(), 'requestor':'Autom'})


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return render_template('index.html')


@socketio.on('username', namespace='/test')
def login(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('log', {'data': 'New user: '+ message['username']}, broadcast=True)
    tasks = Tasks().get_tasks()
    pprint(tasks)
    for task in tasks:
        emit('add_task', {'data': tasks[task]['data'], 'id': task, 'state':tasks[task]['state']})

@socketio.on('take_task', namespace='/test')
def propagate_take_task(message):
    print(message)
    Tasks().modify_task(message['id'], {'username':message['username'], 'state':'ongoing'})
    emit('claimed_task', {'id':message['id'], 'username':message['username'], 'state':'ongoing'}, broadcast=True)

@socketio.on('end_task', namespace='/test')
def propagate_end_Task(message):
    Tasks().modify_task(message['id'], {'state':'done'})
    emit('done_task', {'id':message['id']}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, port=9090, host='127.0.0.1')
