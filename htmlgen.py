from pprint import pprint

class TaskHtml(object):
    def __init__(self, task, task_id):
        self.task = task
        self.task_id = task_id
    def generate(self):
        html_elements=[]
        if self.task['state'] == 'todo':
            priority_colors = {1:'#FF0000', 2:'#DD3300', 3:'#DD8855', 4:'#DDAA77', 5:'#999999'}
            color = priority_colors[self.task['severity']]
            html_elements.append(''' Claim it: <input class="claim" type="submit" value="Claim">''')
        elif self.task['state'] == 'done':
            html_elements.append(''' Solved by: <b>{}</b>'''.format(self.task['claimer']))
            self.task['severity'] = 10 * self.task['severity']
            color = '#00CC00'
        elif self.task['state'] == 'ongoing':
            html_elements.append(''' Claimed by: <b>{}</b> Done: <input class="solved" type="submit" value="Done">'''.format(self.task['claimer']))
            color = '#DBFF70'
        else:
            color = '#00FFFF'
        checks=''.join(html_elements)
        end_code='''<div class="tasks" id="{id}" priority="{priority}" style="background:{color}"> \
<font size="5"><b>Task:</b> {content}</font>
<br>priority: {priority}, Requestor: {requestor} {checks} </div>'''.format(
        id=self.task_id, state=self.task['state'], priority=self.task['severity'], color=color, content=self.task['content'], requestor=self.task['requestor'], checks=checks)
        pprint(end_code)
        return(end_code)
