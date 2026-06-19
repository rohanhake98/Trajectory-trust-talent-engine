document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) return;
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.textContent = 'Processing...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/upload-and-rank', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            renderResults(data.results);
        } else {
            alert('Processing failed: ' + data.message);
        }
    } catch (err) {
        console.error('Error during upload:', err);
        alert('Server connection error.');
    } finally {
        submitBtn.textContent = 'Process & Rank';
        submitBtn.disabled = false;
    }
});

function renderResults(results) {
    const resultsSection = document.getElementById('resultsSection');
    const tbody = document.querySelector('#candidatesTable tbody');
    tbody.innerHTML = '';
    
    results.forEach((c) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${c.rank}</strong></td>
            <td><code>${c.candidate_id}</code></td>
            <td>${parseFloat(c.score).toFixed(3)}</td>
            <td>${c.reasoning}</td>
        `;
        tbody.appendChild(row);
    });
    
    resultsSection.classList.remove('hidden');
}
