document.addEventListener("DOMContentLoaded", function () {

    const canvas = document.getElementById("salesChart");

    if (!canvas) {
        return;
    }


    new Chart(canvas, {

        type: "line",

        data: {

            labels: [
                "Sen",
                "Sel",
                "Rab",
                "Kam",
                "Jum",
                "Sab",
                "Min"
            ],

            datasets: [

                {
                    label: "Penjualan",

                    data: [
                        1250000,
                        1680000,
                        1420000,
                        1950000,
                        1740000,
                        2310000,
                        2150000
                    ],

                    borderWidth: 3,

                    tension: .4,

                    fill: true
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {
                    display: false
                }

            },

            scales: {

                y: {

                    beginAtZero: true,

                    ticks: {

                        callback: function (value) {

                            return "Rp" +
                                (value / 1000000).toFixed(1) +
                                " jt";

                        }

                    }

                }

            }

        }

    });

});