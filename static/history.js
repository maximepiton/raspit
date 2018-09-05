$.ajax({ 
    url: window.location.href + 'forecast', 
    dataType: 'json', 
    async: false, 
    success: function(json){
        raw_json = json
    } 
});

function get_virtual_level(z_in, z_array) {
    for (lvl in z_array) {
        if (z_in < z_array[lvl]) { // we passed over the value
            if (lvl == 0) { return false;  } else {
                return lvl - 1 / (z_array[lvl] - z_array[lvl-1]) * (z_in - z_array[lvl-1]);
            }
        }
    }
    return false;
}

function get_interpolated_value(virtual_level, v_array) {
    return v_array[Math.floor(virtual_level)] + (virtual_level - Math.floor(virtual_level)) *
           (v_array[Math.ceil(virtual_level)] - v_array[Math.floor(virtual_level)]);
}

function get_wind_intensity(u, v) {
    return 3.6*Math.sqrt(Math.pow(u, 2) + Math.pow(v, 2))
}

function get_wind_angle(umet, vmet) {
    return Math.atan2(umet, vmet) * 180 / 3.14 - 90
}

function get_wind_arrow_size(umet, vmet) {
    var font_size = 10 + get_wind_intensity(umet, vmet) / 60 * 35;
    if (font_size < 40) { return font_size } else { return 40 }
}

function get_wind_arrow_color(umet, vmet) {
    var wind_int = get_wind_intensity(umet, vmet);
    if (wind_int < 3) return 'black';
    if (wind_int < 6) return '#0080ff';
    if (wind_int < 10) return '#00ffff';
    if (wind_int < 15) return '#00ff80';
    if (wind_int < 20) return '#00ff00';
    if (wind_int < 25) return '#80ff00';
    if (wind_int < 30) return '#ffff00';
    if (wind_int < 35) return '#ffbf00';
    if (wind_int < 40) return '#ff8000';
    return '#ff0000';
}

var ground = 200;
var max_height = 4000;
var nb_levels = 25;
var levels = [...Array(nb_levels).keys()]; // [0, 1, ... , 24]
var z_levels = levels.map(level => max_height / nb_levels * (level + 1/2));
var nb_hours = Object.keys(raw_json.data).length;

// Table generation
history_table = $('<table></table>').attr({ id: 'history' });

for (var i = nb_levels-1 ; i >= 0; i--) {
    var row = $('<tr></tr>').appendTo(history_table);
    $('<th scope="row"></th>').text(z_levels[i]).appendTo(row);
    for (var j = 0; j < nb_hours; j++) {
        $('<td></td>').attr({ id: ''.concat('l', i, 'h', j) }).appendTo(row);
    }
}

// Column headers
var row = $('<tr></tr>').appendTo(history_table);
$('<td></td>').appendTo(row);

for (hour in raw_json.data) {
    $('<th scope="col"></th>').text(hour).appendTo(row);
}

history_table.appendTo('#history');

var hour_id = 0;
for (hour in raw_json.data) {
    pblh = raw_json.data[hour].pblh;
    for (z in z_levels) {
        virtual_level = get_virtual_level(z_levels[z], raw_json.data[hour].z);
        if (virtual_level == false) {
            $('td#'.concat('l', z, 'h', hour_id)).attr({ bgcolor: 'grey'});
            continue;
        }
        // BL stuff
        if (z_levels[z] < pblh) {
            $('td#'.concat('l', z, 'h', hour_id)).attr({ bgcolor: 'yellow'});
        }

        // Wind stuff
        umet = get_interpolated_value(virtual_level, raw_json.data[hour].umet);
        vmet = get_interpolated_value(virtual_level, raw_json.data[hour].vmet);

        var arrow = $('<div class="wind_arrow"></div>').attr({style: ''.concat('transform: rotate(',
                                                                               get_wind_angle(umet, vmet),
                                                                               'deg); font-size: ',
                                                                               get_wind_arrow_size(umet, vmet),
                                                                               'px; color: ',
                                                                               get_wind_arrow_color(umet, vmet))})
                                                       .text('⮕');
        var wind_int = $('<div class="wind_int"></div>').text(Math.round(get_wind_intensity(umet, vmet)));
        var wind_container = $('<div class="wind_container"></div>').html(arrow).append(wind_int)
        $('td#'.concat('l', z, 'h', hour_id)).html(wind_container);
    }
    hour_id++;
}
