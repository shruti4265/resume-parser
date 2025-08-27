const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');
    const output = document.getElementById('output');
    const loading = document.getElementById('loading');
    const csvDownload = document.getElementById('csvDownload');
    const summaryDownload = document.getElementById('summaryDownload');
    const downloadLinks = document.querySelector('.download-links');
    const tableContainer = document.getElementById('tableContainer');

    const API_URL = 'http://127.0.0.1:5000';

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

      const formData = new FormData();
      for (const file of files) {
        formData.append('files', file);
      }

      try {
        const res = await fetch(`${API_URL}/upload`, {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (res.ok) {
          output.textContent = data.summary;

          csvDownload.href = data.csv_url;
          summaryDownload.href = data.summary_url;
          downloadLinks.style.display = 'flex';

          const table = document.createElement('table');
          const thead = document.createElement('thead');
          thead.innerHTML = '<tr><th>Name</th><th>Email</th><th>Phone</th><th>Skills</th></tr>';
          table.appendChild(thead);

          const tbody = document.createElement('tbody');
          data.results.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
              <td>${item.Name || '-'}</td>
              <td>${item.Email || '-'}</td>
              <td>${item.Phone || '-'}</td>
              <td>${item.Skills || '-'}</td>
            `;
            tbody.appendChild(row);
          });
          table.appendChild(tbody);
          tableContainer.innerHTML = '';
          tableContainer.appendChild(table);
        } else {
          output.textContent = data.error || 'Something went wrong.';
        }
      } catch (err) {
        output.textContent = 'Error connecting to server.';
      }

      loading.style.display = 'none';
      uploadButton.disabled = false;
    });