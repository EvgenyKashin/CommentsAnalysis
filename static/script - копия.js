var commentsData = null;
var cur_comment = 0;
var max_comments = 99;
var answers = [];
var isReadyToPredict = false;

function loadComments() {
	var request = {
		url: "comments",
		type: "GET"
	};
	cur_comment = 0;
	$.ajax(request).done(function(d) {
		commentsData = d;
		$(".col-md-10 p").text(commentsData[cur_comment]);
	});
}

function nextComment() {
	cur_comment += 1;
	if (cur_comment > max_comments) {
		loadComments();
	} else {
		$(".col-md-10 p").text(commentsData[cur_comment]);
	}
}

var entityMap = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
};

function escapeHtml (string) {
  return String(string).replace(/[&<>"'`=\/]/g, function (s) {
    return entityMap[s];
  });
}

function countWords(s){
    s = s.replace(/(^\s*)|(\s*$)/gi,"");//exclude  start and end white-space
    s = s.replace(/[ ]{2,}/gi," ");//2 or more space to 1
    s = s.replace(/\n /,"\n"); // exclude newline with a start spacing
    return s.split(' ').length; 
}

// on document load
$(function() {
	loadComments();
});

// click on next button
$(".col-xs-5 .btn-primary").on("click", function() {
	nextComment();
});

// on textarea input
$(".form-control").on("input", function() {
	$(".col-md-10 .label-warning").text("");
	$("center .label-warning").text("");
});

// click on answer button
$(".col-xs-6 .btn-primary").on("click", function() {
	answer = $(".form-control").val();
	if (countWords(answer) < 2 || answer.length < 5) {
		$(".col-md-10 .label-warning").text("Слишком короткий ответ");
	} else{
		nextComment();
		$(".form-control").val("");
		answers.push(answer);
		$(".col-md-2 h4").text("Ответов: " + answers.length);
		if (answers.length >= 5) {
			isReadyToPredict = true;
			$("#result").removeClass("btn-warning");
			$("#result").addClass("btn-success");
		}
		else {
			isReadyToPredict = false;
		}
	}
});


function resultSuccess(data) {
	if (data) {
		$(".col-md-12 h3").text(data[0]);
		$(".table").html(data[1]);
		$(".col-md-12 h4").text("Зеленый - больше гуманитарный коммент, красный - технарский");
	}
	else {
		$(".col-md-12 h3").text("Что то пошло не так, попробуйте позже(");
	}
}

function resultFailure(data) {
	$(".col-md-12 h3").text("Что то пошло не так, попробуйте позже(");
}

// click on result btn
$("#result").on("click", function() {
	if (isReadyToPredict) {
		data = JSON.stringify(answers);
		var request = {
			url: "predict",
			type: "POST",
			data: data,
			contentType: "application/json; charset=utf-8",
			dataType: "json",
			success: resultSuccess,
			failure: resultFailure
		};
		$.ajax(request);
	} else {
		$("center .label-warning").text("Слишком мало комментариев");
	}
});

// click on restart btn
$("#restart").on("click", function() {
	nextComment();

	answers = [];
	$(".col-md-2 h4").text("Ответов: " + answers.length);

	if (isReadyToPredict) {
		isReadyToPredict = false;
		$("#result").removeClass("btn-success");
		$("#result").addClass("btn-warning");
		$(".col-md-12 h3").text("");
		$(".table").html("");
		$(".col-md-12 h4").text("");
	}
});