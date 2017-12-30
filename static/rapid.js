( function($) {
$(document).ready(function(){
    namespace = '/test';
    var socket = io.connect('http://' + document.domain + ':' + location.port + namespace);

    socket.on('add_task', function(msg) {
	var new_task = $(msg.new_code).draggable();
	$('#todo').prepend(new_task);
	});

    socket.on('log', function(msg) {
	$('#log').append('<br>'+msg.data);
	});


    ///TO THE SERVER SITE!
    $('form#username').submit(function(event) {
	$('#username').hide();
	$('#tasks_main').show();
	$('#add_task_manually').show();
	$('#task_description').focus();
	socket.emit('username', {username: $('#username_field').val()});
	return false;
	});
    
    $('form#add_task_manually').submit(function(event) {
	    socket.emit('add_task_manual', {user: $('#username_field').val(), task_description: $('#task_description').val(), priority: $('#task_priority').val()});
	    return false;
	    });
    $( ".list" ).droppable({
       accept: '.draggable',
       drop: function(ev,ui){
    	    $(ui.draggable).appendTo(this);
    	    //$(ui.draggable).remove();
    	     $(ui.draggable).draggable();
       }
    });
});

} ) ( jQuery );
