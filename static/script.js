
$(document).ready(function() {
	setInterval(loadImages, 2000);
});

function loadImages() {
	$.get('/getimages', function(data) {

		var divs = $('.image');

		divs.each(function(i, item) {
			if (data[i]) {
				$(item).find('img').attr('src',data[i]);
			}
		});


	});
}
