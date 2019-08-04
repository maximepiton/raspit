/** Class representing a daily forecast. */
class Forecast {
    /**
     * Create an instance of forecast
     * 
     * @constructor
     * @param {json} forecast_json Forecast data used to create the object
     */
    constructor(forecast_json) {
        this.raw_json = forecast_json
        this.nb_hours = Object.keys(this.raw_json.forecasts).length;
    }

    /**
     * Get the virtual z-level corresponding to a specific altitude
     * 
     * @param {number} z_in Altitude
     * @param {string} hour Hour
     * @return {number} Virtual z-level
     */
    get_virtual_level(z_in, hour) {
        let z_array = this.raw_json.forecasts[hour].z
        for (let lvl in z_array) {
            if (z_in < z_array[lvl]) { // we passed over the value
                if (lvl == 0) { return false;  } else {
                    return lvl - 1 / (z_array[lvl] - z_array[lvl-1]) * (z_in - z_array[lvl-1]);
                }
            }
        }
        return false;
    }

    /**
     * Get the value of a wrf variable corresponding to a virtual level
     * 
     * @param {number} virtual_level Virtual z-level
     * @param {string} hour Hour
     * @param {string} wrf_var Name of the wrf variable
     * @return {number} Interpolated value
     */
    get_interpolated_wrf_var(virtual_level, hour, wrf_var) {
        console.log(hour);
        console.log(wrf_var);
        let v_array = this.raw_json.forecasts[hour][wrf_var]
        return v_array[Math.floor(virtual_level)] + (virtual_level - Math.floor(virtual_level)) *
              (v_array[Math.ceil(virtual_level)] - v_array[Math.floor(virtual_level)]);
    }

    get_wind_speed(umet, vmet) {
        return 3.6*Math.sqrt(Math.pow(umet, 2) + Math.pow(vmet, 2))
    }

    get_wind_angle(umet, vmet) {
        return Math.atan2(umet, vmet) * 180 / 3.14 - 90
    }

    get_wind_arrow_size(wind_speed) {
        let font_size = 10 + wind_speed / 60 * 35;
        if (font_size < 40) { return font_size } else { return 40 }
    }

    get_wind_arrow_color(wind_speed) {
        if (wind_speed < 3) return 'black';
        if (wind_speed < 6) return '#0080ff';
        if (wind_speed < 10) return '#00ffff';
        if (wind_speed < 15) return '#00ff80';
        if (wind_speed < 20) return '#00ff00';
        if (wind_speed < 25) return '#80ff00';
        if (wind_speed < 30) return '#ffff00';
        if (wind_speed < 35) return '#ffbf00';
        if (wind_speed < 40) return '#ff8000';
        return '#ff0000';
    }

    generate_table(nb_levels, max_height, container_id) {
        let levels = [...Array(nb_levels).keys()]; // [0, 1, ... , 24]
        let z_levels = levels.map(level => max_height / nb_levels * (level + 1/2));
        let rand_id = Math.random().toString(36).substr(2, 7);
        let history_table = $('<table></table>').attr({ id: 'history' });

        for (let i = nb_levels-1 ; i >= 0; i--) {
            let row = $('<tr></tr>').appendTo(history_table);
            $('<th scope="row"></th>').text(z_levels[i]).appendTo(row);
            for (let j = 0; j < this.nb_hours; j++) {
                $('<td></td>').attr({ id: ''.concat('l', i, 'h', j, '_', rand_id) }).appendTo(row);
            }
        }

        // Column headers
        let row = $('<tr></tr>').appendTo(history_table);
        $('<td></td>').appendTo(row);

        for (let hour in this.raw_json.forecasts) {
            $('<th scope="col"></th>').text(hour).appendTo(row);
        }

        history_table.appendTo('#'.concat(container_id));

        let hour_id = 0;
        for (let hour in this.raw_json.forecasts) {
            let pblh = this.raw_json.forecasts[hour].pblh;
            for (let z in z_levels) {
                let virtual_level = this.get_virtual_level(z_levels[z], hour);
                let umet = this.get_interpolated_wrf_var(virtual_level, hour, 'u');
                let vmet = this.get_interpolated_wrf_var(virtual_level, hour, 'v');
                let wind_speed = this.get_wind_speed(umet, vmet)
                let wind_angle = this.get_wind_angle(umet, vmet)

                if (virtual_level == false) {
                    $('td#'.concat('l', z, 'h', hour_id, '_', rand_id)).attr({ bgcolor: 'grey'});
                    continue;
                }
                // BL stuff
                if (z_levels[z] < pblh) {
                    $('td#'.concat('l', z, 'h', hour_id, '_', rand_id)).attr({ bgcolor: 'yellow'});
                }

                // Wind stuff
                let arrow = $('<div class="wind_arrow"></div>').attr({style: ''.concat('transform: rotate(',
                                                                                    wind_angle,
                                                                                    'deg); font-size: ',
                                                                                    this.get_wind_arrow_size(wind_speed),
                                                                                    'px; color: ',
                                                                                    this.get_wind_arrow_color(wind_speed))})
                                                            .text('⮕');
                let wind_speed_html = $('<div class="wind_int"></div>').text(Math.round(wind_speed));
                let wind_container = $('<div class="wind_container"></div>').html(arrow).append(wind_speed_html)
                $('td#'.concat('l', z, 'h', hour_id, '_', rand_id)).html(wind_container);
            }
            hour_id++;
        }
    }
}
