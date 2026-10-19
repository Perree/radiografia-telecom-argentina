function initGoogleChart({
    modalId,        // id del modal Bootstrap
    containerId,    // id del div donde va el gráfico
    packageName,    // paquete de Google Charts (ej: "line", "treemap")
    fetchUrl,       // endpoint que devuelve los datos
    transformData,  // función que recibe la respuesta y devuelve DataTable
    buildChart,     // función que recibe (container, data, options) y devuelve la instancia del chart
    buildOptions,    // función que calcula las opciones dinámicas (según el tamaño, etc.)
    chartEvents // array de eventos a registrar en el chart (ej: ['select', 'ready'])
}) {
    let chartData = null;
    let chart = null;

    google.charts.load('current', { packages: [packageName] });
    google.charts.setOnLoadCallback(fetchData);

    function fetchData() {
        fetch(fetchUrl)
            .then(r => r.json())
            .then(apiResponse => {
                chartData = transformData(apiResponse);
            })
            .catch(err => console.error("Error cargando datos:", err));
    };

    function drawChart() {
        const container = document.getElementById(containerId);
        if (!container || !chartData) return;

        if (!chart) {
            chart = buildChart(container, chartData);
            // Registrar eventos personalizados solo una vez
            if (typeof chartEvents === "function") {
                chartEvents(chart, () => chartData, () => buildOptions(container, chartData));
            }
        }

        const options = buildOptions(container, chartData);

        chart.draw(chartData, options);
    }



    // Redibujar al cambiar tamaño ventana
    window.addEventListener('resize', () => {
        if (chartData) drawChart();
    });

    // Redibujar al abrir modal
    document.addEventListener("DOMContentLoaded", () => {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.addEventListener("shown.bs.modal", () => {
            if (chartData) setTimeout(drawChart, 150);
        });


    });
}