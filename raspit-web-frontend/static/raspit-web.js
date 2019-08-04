var today = new Date();
var date = String(today.getFullYear()) + String(today.getMonth() + 1).padStart(2, '0') + String(today.getDate()).padStart(2, '0');

$.getJSON({
    url: 'https://raspit-forecast-service-xx2xob3mmq-ew.a.run.app/forecast?datetime=' + date + '&lon=1.3722&lat=44.4636',
    success: function (json) {
        const forecast = new Forecast(json);
        forecast.generate_table(25, 4000, 'history');
    }
});