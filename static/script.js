document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const output = document.getElementById('output');
    const loading = document.getElementById('loading');
    const csvDownload = document.getElementById('csvDownload');
    const downloadLinks = document.querySelector('.download-links');
    const tableContainer = document.getElementById('tableContainer');
    const skillsInput = document.getElementById('skillsInput');
    const experienceInput = document.getElementById('experienceInput');
    const chartContainer = document.querySelector('.chart-container');
    const skillsChartCanvas = document.getElementById('skillsChart');
    let skillsChart;
    
    const generateChartCheckbox = document.getElementById('generateChartCheckbox');
    const UPLOAD_URL = '/upload';

    fileInput.addEventListener('change', () => {
        uploadButton.disabled = fileInput.files.length === 0;
    });

    uploadButton.addEventListener('click', async () => {
        const files = fileInput.files;
        if (!files.length) return;
        uploadButton.disabled = true;
        loading.style.display = 'block';
        output.textContent = '';
        tableContainer.innerHTML = '';
        downloadLinks.style.display = 'none';
        chartContainer.style.display = 'none';

        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }
        formData.append('required_skills', skillsInput.value);
        formData.append('min_experience', experienceInput.value || '0');
        formData.append('generate_chart', generateChartCheckbox.checked);

        try {
            const res = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                output.textContent = `Found ${data.results.length} matching resumes.`; 
                downloadLinks.style.display = 'flex';
                const table = document.createElement('table');
                const thead = document.createElement('thead');
                thead.innerHTML = '<tr><th>Name</th><th>Email</th><th>Phone</th><th>Experience</th><th>Skills</th></tr>';
                table.appendChild(thead);
                const tbody = document.createElement('tbody');
                data.results.forEach(item => {
                    const row = document.createElement('tr');
                    const nameCell = document.createElement('td'); nameCell.textContent = item.Name || '-'; row.appendChild(nameCell);
                    const emailCell = document.createElement('td'); emailCell.textContent = item.Email || '-'; row.appendChild(emailCell);
                    const phoneCell = document.createElement('td'); phoneCell.textContent = item.Phone || '-'; row.appendChild(phoneCell);
                    const expCell = document.createElement('td'); expCell.textContent = item.Experience || '0 years'; row.appendChild(expCell);
                    const skillsCell = document.createElement('td'); skillsCell.textContent = item.Skills || '-'; row.appendChild(skillsCell);
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);
                tableContainer.innerHTML = '';
                tableContainer.appendChild(table);
                
                if (data.chart_data && data.chart_data.labels.length > 0) {
                    chartContainer.style.display = 'block';
                    
                    if (skillsChart) {
                        skillsChart.destroy();
                    }
                    
                    skillsChart = new Chart(skillsChartCanvas, {
                        type: 'pie',
                        data: {
                            labels: data.chart_data.labels,
                            datasets: [{
                                label: 'Top Skills',
                                data: data.chart_data.values,
                                // UPDATED: Added many more colors to the palette
                                backgroundColor: [
                                    '#4C78A8', '#F58518', '#E45756', '#72B7B2', '#54A24B',
                                    '#EECA3B', '#B279A2', '#FF9DA6', '#9D755D', '#BAB0AC',
                                    '#AEC7E8', '#FFBB78', '#98DF8A', '#FF9896', '#C5B0D5',
                                    '#C49C94', '#F7B6D2', '#DBDB8D', '#17BECF', '#BCBD22'
                                ],
                                hoverOffset: 4
                            }]
                        }
                    });
                }

            } else {
                output.textContent = `Error: ${data.error || 'Something went wrong.'}`;
            }
        } catch (err) {
            console.error('Fetch error:', err);
            output.textContent = 'Error connecting to the server. Please try again.';
        }

        loading.style.display = 'none';
        uploadButton.disabled = false;
    });
});
