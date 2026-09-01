(function () {
    'use strict';

    let chartsInitialized = false;

    function getJsonData(id, fallback = []) {
        const element = document.getElementById(id);

        if (!element) {
            console.warn(`Chart data element not found: ${id}`);
            return fallback;
        }

        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            console.error(`Failed to parse chart data: ${id}`, error);
            return fallback;
        }
    }

    function destroyChart(name) {
        if (window[name]) {
            try {
                window[name].destroy();
            } catch (error) {
                console.warn(`Could not destroy ${name}`, error);
            }
            window[name] = null;
        }
    }

    // ✅ FIX: theme chart create hone se PEHLE hi padh lo, taaki chart
    // sahi colors ke saath ek hi baar me bane — dobara applyChartTheme()
    // se update() na chalana pade (jo flicker/disappear ka कारण tha)
    function getThemeColors() {
        const mode = localStorage.getItem('theme') || 'light';
        return {
            mode: mode,
            textColor: mode === 'dark' ? '#cbd5e1' : '#374151',
            gridColor: mode === 'dark' ? '#334155' : '#e5e7eb'
        };
    }

    function createTaskChart() {
        const canvas = document.getElementById('taskChart');

        if (!canvas) {
            console.warn('Task chart canvas not found.');
            return;
        }

        const labels = getJsonData('chart-labels-data');
        const completed = getJsonData('completed-series-data');
        const inProgress = getJsonData('in-progress-series-data');
        const overdue = getJsonData('overdue-series-data');
        const theme = getThemeColors();

        destroyChart('taskChartInstance');

        window.taskChartInstance = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Completed',
                        data: completed,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.10)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.35,
                        fill: true
                    },
                    {
                        label: 'In Progress',
                        data: inProgress,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.10)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.35,
                        fill: true
                    },
                    {
                        label: 'Overdue',
                        data: overdue,
                        borderColor: '#f43f5e',
                        backgroundColor: 'rgba(244, 63, 94, 0.08)',
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.35,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            padding: 15,
                            font: { size: 11 },
                            color: theme.textColor
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        ticks: { font: { size: 10 }, color: theme.textColor },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            font: { size: 10 },
                            color: theme.textColor
                        },
                        grid: { color: theme.gridColor }
                    }
                }
            }
        });

        // Ek hi update — chart ab sahi theme ke saath already ban chuka hai
        window.taskChartInstance.update();
    }

    function createProjectChart() {
        const canvas = document.getElementById('projectChart');

        if (!canvas) {
            console.warn('Project chart canvas not found.');
            return;
        }

        const milestoneCounts = getJsonData('milestone-counts-data', {});
        const labels = Object.keys(milestoneCounts);
        const values = Object.values(milestoneCounts);
        const theme = getThemeColors();

        destroyChart('projectChartInstance');

        window.projectChartInstance = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: [
                            '#10b981', '#3b82f6', '#f59e0b',
                            '#8b5cf6', '#ef4444', '#06b6d4'
                        ],
                        borderWidth: 0,
                        hoverOffset: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            padding: 12,
                            font: { size: 11 },
                            color: theme.textColor
                        }
                    }
                }
            }
        });

        window.projectChartInstance.update();
    }

    function createTeamChart() {
        const canvas = document.getElementById('teamChart');

        if (!canvas) {
            console.warn('Team chart canvas not found.');
            return;
        }

        const teamData = getJsonData('team-distribution-data', []);
        const theme = getThemeColors();

        destroyChart('teamChartInstance');

        const labels = teamData.map(item => item.label);
        const values = teamData.map(item => item.value);

        window.teamChartInstance = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: [
                            '#3b82f6', '#8b5cf6', '#10b981',
                            '#f59e0b', '#f43f5e', '#06b6d4'
                        ],
                        borderWidth: 0,
                        hoverOffset: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            boxHeight: 10,
                            padding: 10,
                            font: { size: 10 },
                            color: theme.textColor
                        }
                    }
                }
            }
        });

        window.teamChartInstance.update();
    }

    function initializeCharts() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded. Make sure the Chart.js CDN is available.');
            return;
        }

        try { createTaskChart(); } catch (error) { console.error('Task chart initialization failed:', error); }
        try { createProjectChart(); } catch (error) { console.error('Project chart initialization failed:', error); }
        try { createTeamChart(); } catch (error) { console.error('Team chart initialization failed:', error); }

        // Layout fully settle hone ke baad ek extra resize — safe net,
        // isse chart.data ko haath nahi lagta, sirf sizing theek hoti hai
        requestAnimationFrame(() => {
            if (window.taskChartInstance) window.taskChartInstance.resize();
            if (window.projectChartInstance) window.projectChartInstance.resize();
            if (window.teamChartInstance) window.teamChartInstance.resize();
        });

        chartsInitialized = true;

        // ✅ FIX: yahan se applyChartTheme() ka dobara call hata diya —
        // charts ab creation ke waqt hi sahi theme colors ke saath ban
        // chuke hain. Isliye ek extra update() nahi chalta aur data
        // flicker/disappear nahi hota. applyChartTheme() sirf tab
        // chalega jab USER manually theme toggle button dabayega
        // (setTheme() ke through) — us waqt sirf colors update honge,
        // data ko haath nahi lagega.
    }

    function waitForChartJs() {
        if (typeof Chart !== 'undefined') {
            initializeCharts();
            return;
        }

        let attempts = 0;
        const interval = setInterval(() => {
            attempts++;
            if (typeof Chart !== 'undefined') {
                clearInterval(interval);
                initializeCharts();
                return;
            }
            if (attempts >= 50) {
                clearInterval(interval);
                console.error('Chart.js could not be loaded after waiting.');
            }
        }, 100);
    }

    window.applyOverviewFilters = function () {
        const params = new URLSearchParams();

        const range = document.getElementById('rangeSelect');
        const department = document.getElementById('filter_department');
        const status = document.getElementById('filter_status');
        const priority = document.getElementById('filter_priority');
        const assignee = document.getElementById('filter_assignee');
        const milestone = document.getElementById('filter_milestone');

        if (range && range.value) params.set('range', range.value);
        if (department && department.value) params.set('department', department.value);
        if (status && status.value) params.set('status', status.value);
        if (priority && priority.value) params.set('priority', priority.value);
        if (assignee && assignee.value) params.set('assignee', assignee.value);
        if (milestone && milestone.value) params.set('milestone', milestone.value);

        fetch(`/tasks/api/overview-data/?${params.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.error) {
                console.error('Overview API error:', data.error);
                return;
            }

            const kpis = {
                kpi_total_users: data.total_users,
                kpi_active_projects: data.active_projects,
                kpi_tasks_in_progress: data.tasks_in_progress,
                kpi_tasks_completed: data.tasks_completed,
                kpi_overdue_tasks: data.overdue_tasks
            };

            Object.entries(kpis).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value;
            });

            if (window.taskChartInstance) {
                window.taskChartInstance.data.labels = data.chart_labels || [];
                window.taskChartInstance.data.datasets[0].data = data.completed_series || [];
                window.taskChartInstance.data.datasets[1].data = data.in_progress_series || [];
                window.taskChartInstance.data.datasets[2].data = data.overdue_series || [];
                window.taskChartInstance.update();
            }

            if (window.projectChartInstance) {
                const milestoneCounts = data.milestone_counts || {};
                window.projectChartInstance.data.labels = Object.keys(milestoneCounts);
                window.projectChartInstance.data.datasets[0].data = Object.values(milestoneCounts);
                window.projectChartInstance.update();
            }

            if (window.teamChartInstance && Array.isArray(data.team_distribution)) {
                window.teamChartInstance.data.labels = data.team_distribution.map(item => item.label);
                window.teamChartInstance.data.datasets[0].data = data.team_distribution.map(item => item.value);
                window.teamChartInstance.update();
            }

            const queryString = params.toString();
            window.history.replaceState(
                {}, '', queryString ? `${window.location.pathname}?${queryString}` : window.location.pathname
            );
        })
        .catch(error => {
            console.error('Failed to load overview data:', error);
        });
    };

    window.onRangeChange = function () {
        const range = document.getElementById('rangeSelect');
        const customFields = document.getElementById('customRangeFields');

        if (!range || !customFields) return;

        if (range.value === 'custom') {
            customFields.classList.remove('hidden');
        } else {
            customFields.classList.add('hidden');
        }
    };

    window.clearOverviewFilters = function () {
        const rangeSelect = document.getElementById('rangeSelect');
        const customFields = document.getElementById('customRangeFields');

        const startInput = document.querySelector(
            '#customRangeFields input[name="start"]'
        );

        const endInput = document.querySelector(
            '#customRangeFields input[name="end"]'
        );

        if (rangeSelect) {
            rangeSelect.value = '7';
        }

        if (customFields) {
            customFields.classList.add('hidden');
        }

        if (startInput) {
            startInput.value = '';
        }

        if (endInput) {
            endInput.value = '';
        }

        [
            'filter_department',
            'filter_status',
            'filter_priority',
            'filter_assignee',
            'filter_milestone'
        ].forEach(function (id) {
            const element = document.getElementById(id);

            if (element) {
                element.value = '';
            }
        });

        if (typeof window.applyOverviewFilters === 'function') {
            window.applyOverviewFilters();
        } else {
            console.error('applyOverviewFilters is not available.');
        }
    };


    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', waitForChartJs);
    } else {
        waitForChartJs();
    }

})();