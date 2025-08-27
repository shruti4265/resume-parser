document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const output = document.getElementById('output');
    const loading = document.getElementById('loading');
    const csvDownload = document.getElementById('csvDownload');
    const summaryDownload = document.getElementById('summaryDownload');
    const downloadLinks = document.querySelector('.download-links');
    const tableContainer = document.getElementById('tableContainer');

    // By removing the hardcoded URL, this will work both locally and when deployed.
    const UPLOAD_URL = '/upload';
    const CSV_DOWNLOAD_URL = '/download/csv';
    const SUMMARY_DOWNLOAD_URL = '/download/summary';

    fileInput.addEventListener('change', () => {
        uploadButton.disabled = fileInput.files.length === 0;
        output.textContent = '';
        downloadLinks.style.display = 'none';
        tableContainer.innerHTML = '';

        if (fileInput.files.length > 0) {
            const fileNames = Array.from(fileInput.files).map(f => `• ${f.name}`).join('\n');
            output.textContent = `Selected Files:\n${fileNames}`;
        }
    });

    uploadButton.addEventListener('click', async () => {
        const files = fileInput.files;
        if (!files.length) return;

        uploadButton.disabled = true;
        loading.style.display = 'block';
        output.textContent = '';
        tableContainer.innerHTML = '';
        downloadLinks.style.display = 'none';

        const formData = new FormData();
        for (const file of files) {
            formData.append('files', file);
        }

        try {
            const res = await fetch(UPLOAD_URL, {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                output.textContent = data.summary;

                // Update download links to point to the new routes
                csvDownload.href = CSV_DOWNLOAD_URL;
                summaryDownload.href = SUMMARY_DOWNLOAD_URL;
                downloadLinks.style.display = 'flex';

                // --- Build the results table (no changes here) ---
                const table = document.createElement('table');
                const thead = document.createElement('thead');
                thead.innerHTML = '<tr><th>Name</th><th>Email</th><th>Phone</th><th>Skills</th></tr>';
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                data.results.forEach(item => {
                    const row = document.createElement('tr');
                    // Use textContent for security instead of innerHTML
                    const nameCell = document.createElement('td');
                    nameCell.textContent = item.Name || '-';
                    row.appendChild(nameCell);
                    
                    const emailCell = document.createElement('td');
                    emailCell.textContent = item.Email || '-';
                    row.appendChild(emailCell);
                    
                    const phoneCell = document.createElement('td');
                    phoneCell.textContent = item.Phone || '-';
                    row.appendChild(phoneCell);
                    
                    const skillsCell = document.createElement('td');
                    skillsCell.textContent = item.Skills || '-';
                    row.appendChild(skillsCell);

                    tbody.appendChild(row);
                });
                table.appendChild(tbody);
                tableContainer.innerHTML = '';
                tableContainer.appendChild(table);
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
