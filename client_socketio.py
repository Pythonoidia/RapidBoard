from socketIO_client import SocketIO, BaseNamespace

class TaskNamespace(BaseNamespace):
    pass

socketio =  SocketIO('localhost', 9095)
task_namespace = socketio.define(TaskNamespace, '/task')
task_namespace.emit('add_task', {'content':'Example task', 'severity':3})


