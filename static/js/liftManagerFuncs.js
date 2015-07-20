function addMoreLift(selector, addAfter, type, entry) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + type + '-TOTAL_FORMS').val();
    
    newElement.attr({'id': newElement.attr('id').replace(RegExp('-[0-9]*'), '-'+total)});
    
    // Handle all other input fields
    newElement.find('input').each(function() {
        var name = $(this).attr('name').replace(RegExp('-[0-9]*-'),'-'+total+'-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id});
        $(this).val('').removeAttr('checked');
    });
    
    // Empty other cells
    newElement.find('td').each(function() {
        var className = $(this).attr('class');
        if (className != 'liftManager-name') {
            $(this).text('');
        }
    });
    
    newElement.show();
    
    total++;
    $('#id_' + type + '-TOTAL_FORMS').val(total);
    $(addAfter).after(newElement);
}

$(document).ready(function() {
	
	// Hide all unused/deleted rows in log
	$("tr.liftList").each(function() {
		var emptyCounter = 0; // Unused rows are completely empty. emptyCounter determines whether a row is empty or not.
		
		$(this).find('input').each(function() {
			if ($(this).attr('type') == 'text') {
				if (!$(this).val()) {
					emptyCounter += 1;
				}
			}
			if ($(this).attr('type') == 'checkbox') {
                if (!$(this).attr('checked')) {
                    emptyCounter += 1;
                }
			}
		});
		
		if (emptyCounter >= 2) { // Hard coded based on number of fields in StrengthForm
			$(this).hide();
		}
	});
});