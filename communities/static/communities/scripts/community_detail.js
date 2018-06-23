var ctx = document.getElementById("history").getContext('2d');
var myChart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: [{
            label: 'followers',
            data: followers_history
        }]
    },
    options: {
        legend: {
            display: false
        },
        title: {
            display: true,
            text: 'Followers'
        },
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    unit: 'day'
                }
            }]
        }
    }
});
