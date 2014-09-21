from __future__ import print_function
from gevent import monkey
monkey.patch_all()

import time
from threading import Thread
from flask import Flask, render_template, session
from flask.ext.socketio import SocketIO, emit
import datetime
import Queue

from pprint import pprint
import random


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None
task_queue = Queue.Queue(0)

class Tasks(object):
    _tasks = {}
    _id = []
    '''
    We are Borg.
    ####Task:
    'id': #unique
    {timestamp:'date',
    task:'information about task',
    severity:'1-6', #where 1 is the highest, defines color of background
    ####solver:'username',  NOT NEEDED ANYMORE, as claimer == solver
    claimer:'username',
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
        id = int(id)
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
        '''
        html_elements=[]
        if task['state'] == 'todo':
            priority_colors = {1:'#FF0000', 2:'#DD3300', 3:'#DD8855', 4:'#DDAA77', 5:'#999999'}
            color = priority_colors[task['severity']]
            html_elements.append(''' Claim it: <input class="claim" type="submit" value="Claim">'''.format(id=id))
        elif task['state'] == 'done':
            html_elements.append(''' Solved by: <b>{}</b>'''.format(task['claimer']))
            color = '#00CC00'
        elif task['state'] == 'ongoing':
            html_elements.append(''' Claimed by: <b>{}</b> Done: <input class="solved" type="submit" value="Done">'''.format(task['claimer']))
            color = '#DBFF70'
        else:
            color = '#00FFFF'
        checks=''.join(html_elements)

        end_code='''<div class="tasks" id='{id}' style="background:{color}"> \
<font size="5"><b>Task:</b> {content}</font>
<br>priority: {priority}, Requestor: {requestor} {checks} </div>'''.format(
        id=id, state=task['state'], priority=task['severity'], color=color, content=task['content'], requestor=task['requestor'], checks=checks)
        pprint(end_code)
        if one_user:
            if modify:
                emit.emit('replace_task',  {'id':id, 'new_code':end_code})
            else:
                emit('add_task', {'new_code':end_code})
        else:
            if modify:
                socketio.emit('replace_task',  {'id':id, 'new_code':end_code}, namespace='/test')
            else:
                socketio.emit('add_task', {'new_code':end_code}, namespace='/test')
            #emit('replace_task', {'id':id, 'new_code':end_code}, broadcast=True)

    def emit_all_tasks(self):
        for task in self._tasks:
            self.emit_task(task, self._tasks[task], one_user=True)
    



def example_producer_thread():
    global task_queue
    while True:
        line = 'Errytime the same!'
        task={'content': line, 'severity':random.randint(1, 5)}
        pprint('Producing: ')
        pprint(task)
        task_queue.put(task)
        time.sleep(random.randint(3, 8))

def consumer_thread():
    """This thread should be an queue consumer
    Consuming instances put into queue bar multiple other watchers"""
    global task_queue
    while True:
        while not task_queue.empty():
            time.sleep(1)
            task = task_queue.get()
            pprint('Consuming: ')
            pprint(task)
            Tasks().add_task({'content': task['content'], 'severity':task['severity']})
        time.sleep(1)


@app.route('/')
def index():


    return render_template('index.html')


@socketio.on('username', namespace='/test')
def login(message):
    emit('log', {'data': 'New user: '+ message['username']}, broadcast=True)
    Tasks().emit_all_tasks()

@socketio.on('take_task', namespace='/test')
def propagate_take_task(message):
    Tasks().modify_task(message['id'], {'claimer':message['user'], 'state':'ongoing'})

@socketio.on('end_task', namespace='/test')
def propagate_end_task(message):
    Tasks().modify_task(message['id'], {'state':'done'})

if __name__ == '__main__':
    producer = Thread(target=example_producer_thread)
    producer.start()
    consumer = Thread(target=consumer_thread)
    consumer.start()
    socketio.run(app, port=9095, host='localhost')
    
