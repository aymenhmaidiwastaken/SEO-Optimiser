function reportApp() {
    return {
        tab: 'issues',
        issueFilter: { severity: '', category: '' },

        init() {
            this.$watch('issueFilter', () => this.filterIssues());
        },

        filterIssues() {
            const rows = document.querySelectorAll('.issue-row');
            rows.forEach(row => {
                const sev = row.dataset.severity;
                const cat = row.dataset.category;
                const showSev = !this.issueFilter.severity || sev === this.issueFilter.severity;
                const showCat = !this.issueFilter.category || cat === this.issueFilter.category;
                row.style.display = (showSev && showCat) ? '' : 'none';
            });
        }
    };
}

function initCharts(overallScore, scores) {
    // Overall gauge
    const gaugeCtx = document.getElementById('overallGauge');
    if (gaugeCtx) {
        new Chart(gaugeCtx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [overallScore, 100 - overallScore],
                    backgroundColor: [
                        overallScore >= 80 ? '#22c55e' : overallScore >= 50 ? '#eab308' : '#ef4444',
                        '#e5e7eb'
                    ],
                    borderWidth: 0,
                }]
            },
            options: {
                cutout: '75%',
                responsive: true,
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
                rotation: -90,
                circumference: 180,
            }
        });
    }

    // Radar chart
    const radarCtx = document.getElementById('radarChart');
    if (radarCtx && scores.length > 0) {
        const labels = scores.map(s => s.category);
        const data = scores.map(s => s.score);

        new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Score',
                    data: data,
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    borderColor: 'rgba(79, 70, 229, 0.8)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(79, 70, 229, 1)',
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { stepSize: 20, display: false },
                        grid: { color: '#e5e7eb' },
                        pointLabels: { font: { size: 11 } },
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }
}
