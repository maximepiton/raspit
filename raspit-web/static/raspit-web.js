for (let i = 0 ; i < 3 ; i++) {
    $.getJSON({ 
        url: window.location.href + 'forecast',
        data: {'last_x_day': i},
        success: function(json){
            const forecast = new Forecast(json);
            forecast.generate_table(25, 4000, 'history');
        } 
    });
}