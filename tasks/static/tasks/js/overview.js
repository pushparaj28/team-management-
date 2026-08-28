function applyOverviewFilters() {
  const params = new URLSearchParams();
  ['range', 'department', 'status', 'priority', 'assignee', 'milestone'].forEach(id => {
    const el = document.getElementById(`filter_${id}`);
    if (el && el.value) params.set(id, el.value);
  });

  fetch(`/tasks/api/overview-data/?${params.toString()}`)
    .then(res => res.json())
    .then(data => {
      if (data.error) return;

      document.getElementById('kpi_total_users').textContent = data.total_users;
      document.getElementById('kpi_active_projects').textContent = data.active_projects;
      document.getElementById('kpi_in_progress').textContent = data.tasks_in_progress;
      document.getElementById('kpi_completed').textContent = data.tasks_completed;
      document.getElementById('kpi_overdue').textContent = data.overdue_tasks;

      if (window.taskChartInstance) {
        taskChartInstance.data.labels = data.chart_labels;
        taskChartInstance.data.datasets[0].data = data.completed_series;
        taskChartInstance.data.datasets[1].data = data.in_progress_series;
        taskChartInstance.data.datasets[2].data = data.overdue_series;
        taskChartInstance.update();
      }
      if (window.projectChartInstance) {
        projectChartInstance.data.labels = Object.keys(data.milestone_counts);
        projectChartInstance.data.datasets[0].data = Object.values(data.milestone_counts);
        projectChartInstance.update();
      }

      window.history.replaceState({}, '', `${window.location.pathname}?${params.toString()}`);
    });
}