<script>
import { useLayout } from '@/layout/composables/layout';
import Chart from 'primevue/chart';

export default {
    components: {
        Chart
    },
    props: {
        campagnes: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            chartData: null,
            chartOptions: null,
            groupByYear: false, // New state for toggling grouping
            isDarkTheme: useLayout().isDarkTheme, // Add this line to track the theme
            primaryColor: useLayout().getPrimary,
            zoomLevel: window.devicePixelRatio || 1 // Track the zoom level
        };
    },
    mounted() {
        this.chartOptions = this.setChartOptions();
        this.updateChartData();
        window.addEventListener('resize', this.handleResize);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize);
    },
    watch: {
        campagnes: {
            handler() {
                this.updateChartData();
            },
            deep: true,
            immediate: true
        },
        isDarkTheme(newVal) {
            this.chartOptions = this.setChartOptions(); // Update chart options when theme changes
            this.updateChartData(); // Optionally update chart data if needed
        },
        primaryColor(newVal) {
            this.chartOptions = this.setChartOptions(); // Update chart options when primary color changes
            this.updateChartData(); // Optionally update chart data if needed
        },
        zoomLevel(newVal) {
            this.chartOptions = this.setChartOptions(); // Update chart options when zoom level changes
        }
    },
    methods: {
        handleResize() {
            this.zoomLevel = window.devicePixelRatio || 1;
        },
        updateChartData() {
            this.chartData = this.groupByYear ? this.setChartDataByYear() : this.setChartDataBySemester();
        },
        setChartDataBySemester() {
            const documentStyle = getComputedStyle(document.documentElement);
            const sortedCampagnes = [...this.campagnes].sort((a, b) => a.trimestre - b.trimestre);
            const labels = sortedCampagnes.map((campagne) => this.formatTrimestre(campagne.trimestre));
            const cycle1Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_candidature_cycle1);
            const cycle2Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_candidature_cycle2);
            const cycle3Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_candidature_cycle3);
            const totalCostData = sortedCampagnes.map((campagne) => campagne.stats.cout_total);
            const assistantCycle1Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_assistant_cycle1);
            const assistantCycle2Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_assistant_cycle2);
            const assistantCycle3Data = sortedCampagnes.map((campagne) => campagne.stats.nbr_assistant_cycle3);
            const totalTpData = sortedCampagnes.map((campagne) => campagne.stats.nbr_tp_total);
            const totalTdData = sortedCampagnes.map((campagne) => campagne.stats.nbr_td_total);

            return {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 1',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-500'),
                        data: cycle1Data,
                        stack: 'candidature',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 2',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-600'),
                        data: cycle2Data,
                        stack: 'candidature',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 3',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-900'),
                        data: cycle3Data,
                        stack: 'candidature',
                        barThickness: 52
                    },
                    {
                        type: 'line',
                        label: 'Coût total',
                        fill: false,
                        borderColor: documentStyle.getPropertyValue('--p-primary-color'),
                        yAxisID: 'y1',
                        tension: 0.4,
                        data: totalCostData
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 1',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-500'),
                        data: assistantCycle1Data,
                        stack: 'assistant',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 2',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-600'),
                        data: assistantCycle2Data,
                        stack: 'assistant',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 3',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-900'),
                        data: assistantCycle3Data,
                        stack: 'assistant',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Total TP',
                        backgroundColor: documentStyle.getPropertyValue('--p-purple-500'),
                        data: totalTpData,
                        stack: 'activite',
                        barThickness: 52
                    },
                    {
                        type: 'bar',
                        label: 'Total TD',
                        backgroundColor: documentStyle.getPropertyValue('--p-indigo-500'),
                        data: totalTdData,
                        stack: 'activite',
                        barThickness: 52
                    }
                ]
            };
        },
        setChartDataByYear() {
            const documentStyle = getComputedStyle(document.documentElement);
            const groupedData = this.campagnes.reduce((acc, campagne) => {
                const year = campagne.trimestre.toString().substring(0, 4);
                if (!acc[year]) {
                    acc[year] = {
                        cycle1: 0,
                        cycle2: 0,
                        cycle3: 0,
                        totalCost: 0,
                        assistantCycle1: 0,
                        assistantCycle2: 0,
                        assistantCycle3: 0
                    };
                }
                acc[year].cycle1 += campagne.stats.nbr_candidature_cycle1;
                acc[year].cycle2 += campagne.stats.nbr_candidature_cycle2;
                acc[year].cycle3 += campagne.stats.nbr_candidature_cycle3;
                acc[year].totalCost += campagne.stats.cout_total;
                acc[year].assistantCycle1 += campagne.stats.nbr_assistant_cycle1;
                acc[year].assistantCycle2 += campagne.stats.nbr_assistant_cycle2;
                acc[year].assistantCycle3 += campagne.stats.nbr_assistant_cycle3;
                acc[year].nbr_tp_total = campagne.stats.nbr_tp_total;
                acc[year].nbr_td_total = campagne.stats.nbr_td_total;

                return acc;
            }, {});

            const labels = Object.keys(groupedData).sort();
            const cycle1Data = labels.map((year) => groupedData[year].cycle1);
            const cycle2Data = labels.map((year) => groupedData[year].cycle2);
            const cycle3Data = labels.map((year) => groupedData[year].cycle3);
            const totalCostData = labels.map((year) => groupedData[year].totalCost);
            const assistantCycle1Data = labels.map((year) => groupedData[year].assistantCycle1);
            const assistantCycle2Data = labels.map((year) => groupedData[year].assistantCycle2);
            const assistantCycle3Data = labels.map((year) => groupedData[year].assistantCycle3);
            const totalTpData = labels.map((year) => groupedData[year].nbr_tp_total);
            const totalTdData = labels.map((year) => groupedData[year].nbr_td_total);

            return {
                labels: labels,
                datasets: [
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 1',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-500'),
                        data: cycle1Data,
                        stack: 'candidature'
                    },
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 2',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-600'),
                        data: cycle2Data,
                        stack: 'candidature'
                    },
                    {
                        type: 'bar',
                        label: 'Candidature Cycle 3',
                        backgroundColor: documentStyle.getPropertyValue('--p-red-900'),
                        data: cycle3Data,
                        stack: 'candidature'
                    },
                    {
                        type: 'line',
                        label: 'Total Cost',
                        fill: false,
                        borderColor: documentStyle.getPropertyValue('--p-primary-color'),
                        yAxisID: 'y1',
                        tension: 0.4,
                        data: totalCostData
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 1',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-500'),
                        data: assistantCycle1Data,
                        stack: 'assistant'
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 2',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-600'),
                        data: assistantCycle2Data,
                        stack: 'assistant'
                    },
                    {
                        type: 'bar',
                        label: 'Assistant Cycle 3',
                        backgroundColor: documentStyle.getPropertyValue('--p-green-900'),
                        data: assistantCycle3Data,
                        stack: 'assistant'
                    },
                    {
                        type: 'bar',
                        label: 'Total TP',
                        backgroundColor: documentStyle.getPropertyValue('--p-purple-500'),
                        data: totalTpData,
                        stack: 'activite'
                    },
                    {
                        type: 'bar',
                        label: 'Total TD',
                        backgroundColor: documentStyle.getPropertyValue('--p-indigo-500'),
                        data: totalTdData,
                        stack: 'activite'
                    }
                ]
            };
        },
        setChartOptions() {
            const documentStyle = getComputedStyle(document.documentElement);
            const textColor = documentStyle.getPropertyValue('--p-text-color');
            const textColorSecondary = documentStyle.getPropertyValue('--p-text-muted-color');
            const surfaceBorder = documentStyle.getPropertyValue('--p-content-border-color');

            return {
                stacked: false,
                maintainAspectRatio: false,
                aspectRatio: 0.8,
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        align: 'end',
                        labels: {
                            generateLabels: (chart) => {
                                const datasets = chart.data.datasets;
                                const groups = {
                                    candidature: [],
                                    assistant: [],
                                    activite: []
                                };

                                datasets.forEach((dataset, index) => {
                                    const group = dataset.stack;
                                    if (groups[group]) {
                                        groups[group].push({
                                            text: dataset.label,
                                            fillStyle: dataset.backgroundColor,
                                            hidden: !chart.isDatasetVisible(index),
                                            datasetIndex: index
                                        });
                                    }
                                });

                                return [
                                    { text: 'Candidature', children: groups.candidature, fillStyle: 'red', fontColor: textColor, strokeStyle: 'red' },
                                    { text: 'Assistant', children: groups.assistant, fillStyle: 'green', fontColor: textColor, strokeStyle: 'green' },
                                    { text: 'Activité', children: groups.activite, fillStyle: 'purple', fontColor: textColor, strokeStyle: 'purple' },
                                    { text: 'Coût', datasetIndex: 3, fillStyle: documentStyle.getPropertyValue('--p-primary-color'), fontColor: textColor, strokeStyle: documentStyle.getPropertyValue('--p-primary-color') }
                                ];
                            }
                        },
                        onClick: (e, legendItem, legend) => {
                            const ci = legend.chart;
                            const datasets = ci.data.datasets;

                            if (legendItem.children) {
                                // Toggle visibility of all datasets in the group
                                const visibility = !legendItem.children.every((child) => ci.getDatasetMeta(child.datasetIndex).hidden);
                                legendItem.children.forEach((child) => {
                                    ci.getDatasetMeta(child.datasetIndex).hidden = visibility;
                                });
                            } else {
                                // Toggle visibility of the individual dataset
                                const index = legendItem.datasetIndex;
                                ci.getDatasetMeta(index).hidden = !ci.getDatasetMeta(index).hidden;
                            }

                            ci.update();
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            color: surfaceBorder
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        stacked: true,
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            color: surfaceBorder
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            color: textColorSecondary
                        },
                        grid: {
                            drawOnChartArea: false,
                            color: surfaceBorder
                        },
                        ticks: {
                            // Include a dollar sign in the ticks
                            callback: function (value, index, ticks) {
                                return '$' + value;
                            }
                        }
                    }
                }
            };
        },
        toggleGrouping() {
            this.groupByYear = !this.groupByYear;
            this.updateChartData();
        },
        formatTrimestre(value) {
            value = value + '';
            let season = value.charAt(4);
            let year = value.substring(0, 4);

            switch (season) {
                case '1':
                    return 'Hiver ' + year;
                case '2':
                    return 'Été ' + year;
                case '3':
                    return 'Automne ' + year;
                default:
                    break;
            }
        },
        exportCSV() {
            const csvData = this.campagnes.map((campagne) => {
                return {
                    trimestre: campagne.trimestre,
                    cycle1: campagne.stats.nbr_candidature_cycle1,
                    cycle2: campagne.stats.nbr_candidature_cycle2,
                    cycle3: campagne.stats.nbr_candidature_cycle3,
                    coutTotal: campagne.stats.cout_total,
                    assistantCycle1: campagne.stats.nbr_assistant_cycle1,
                    assistantCycle2: campagne.stats.nbr_assistant_cycle2,
                    assistantCycle3: campagne.stats.nbr_assistant_cycle3
                };
            });

            const headers = Object.keys(csvData[0]).join(',');
            const rows = csvData.map((row) => Object.values(row).join(',')).join('\n');
            const csvContent = 'data:text/csv;charset=utf-8,' + headers + '\n' + rows;

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', 'campagnes.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
};
</script>

<template>
    <div>
        <div class="flex flex-wrap items-center justify-between">
            <Button class="m-4" label="Exporter" size="small" icon="pi pi-upload" severity="secondary" @click="exportCSV($event)" />
            <ToggleButton class="m-4" size="small" onLabel="Par année" offLabel="Par trimestre" @click="toggleGrouping" />
        </div>
        <Chart type="bar" :data="chartData" :options="chartOptions" class="h-[20rem]" />
    </div>
</template>
