(function() {

    var field_name2option = find_options();
    var field_name2sorting_icon = find_sorting_icons();
    sync_sorting_icons();
    init_events();


    function find_options() {
        var res = {};
        var options = document.forms['filter'].elements["sort_by"].options;
        for (var i=0; i<options.length; ++i) {
            option = options[i];
            res[option.value] = option;
        }
        return res;
    }

    function find_sorting_icons() {
        var res = {};
        res['followers'] = document.getElementById('followers-range-widget').getElementsByClassName('filter__sorting-icon')[0];
        res['views_per_post'] = document.getElementById('views-range-widget').getElementsByClassName('filter__sorting-icon')[0];
        res['likes_per_view'] = document.getElementById('likes-range-widget').getElementsByClassName('filter__sorting-icon')[0];
        return res;
    }

    function set_sorting_field(field_name) {
        disable_sorting_icons_except(field_name);
        toggle_sorting_field(field_name);
        sync_options();
    }

    function disable_sorting_icons_except(field_name) {
        for (var fn in field_name2sorting_icon) {
            if (fn != field_name) {
                field_name2sorting_icon[fn].classList.add('filter__sorting-icon--disabled');
            }
        }
    }

    function toggle_sorting_field(field_name) {
        var sorting_icon = field_name2sorting_icon[field_name];
        if (sorting_icon.classList.contains('filter__sorting-icon--disabled')) {
            sorting_icon.classList.remove('filter__sorting-icon--disabled');
        } else if (sorting_icon.classList.contains('filter__sorting-icon--up')) {
            sorting_icon.classList.remove('filter__sorting-icon--up');
            sorting_icon.classList.add('filter__sorting-icon--down');
        } else if (sorting_icon.classList.contains('filter__sorting-icon--down')) {
            sorting_icon.classList.remove('filter__sorting-icon--down');
            sorting_icon.classList.add('filter__sorting-icon--up');
        } else {
            /* an unexpected error */
        }
    }

    function sync_options() {
        for (var field_name in field_name2sorting_icon) {
            var sorting_icon = field_name2sorting_icon[field_name];
            if (sorting_icon.classList.contains('filter__sorting-icon--disabled')) {
                field_name2option[field_name].selected = false;
            } else {
                field_name2option[field_name].selected = true;
                var inverse = document.forms["filter"].elements["inverse"];
                if (sorting_icon.classList.contains('filter__sorting-icon--up')) {
                    inverse.checked = false;
                } else if (sorting_icon.classList.contains('filter__sorting-icon--down')) {
                    inverse.checked = true;
                } else {
                    /* an unexpected error */
                }
            }
        }
    }

    function init_events() {
        for (var field_name in field_name2sorting_icon) {
            var sorting_icon = field_name2sorting_icon[field_name];
            (function(field_name){
                sorting_icon.onclick = function() {
                    set_sorting_field(field_name);
                };
            })(field_name);
        }
    }

    function sync_sorting_icons() {
        var current_field_name = document.forms['filter'].elements["sort_by"].selectedOptions[0].value;
        for (var field_name in field_name2sorting_icon) {
            var sorting_icon = field_name2sorting_icon[field_name];
            if (field_name == current_field_name) {
                sorting_icon.classList.remove('filter__sorting-icon--disabled');
                if (document.forms["filter"].elements["inverse"].checked) {
                    sorting_icon.classList.remove('filter__sorting-icon--up');
                    sorting_icon.classList.add('filter__sorting-icon--down');
                } else {
                    sorting_icon.classList.remove('filter__sorting-icon--down');
                    sorting_icon.classList.add('filter__sorting-icon--up');
                }
            } else {
                sorting_icon.classList.remove('filter__sorting-icon--down');
                sorting_icon.classList.add('filter__sorting-icon--up');
                sorting_icon.classList.add('filter__sorting-icon--disabled');
            }
        }
    }
})();
