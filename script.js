document.getElementById('resumeForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const jobDescription = document.getElementById('job-description').value;
    const resumes = document.getElementById('resume-upload').files;
    const loading = document.getElementById('loading');
    const resultsTable = document.getElementById('resultsTable');

    if (!jobDescription || resumes.length === 0) {
        alert('Please provide a job description and at least one resume.');
        return;
    }

    // Show loading message
    loading.classList.remove('hidden');

    // Prepare form data
    const formData = new FormData();
    formData.append('jobDescription', jobDescription);
    for (let i = 0; i < resumes.length; i++) {
        formData.append('resumes', resumes[i]);
    }

    try {
        // Send data to backend
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to process resumes.');
        }

        const data = await response.json();

        // Clear previous results
        resultsTable.innerHTML = '';

        // Populate results table
        data.forEach((item, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${item.Resume}</td>
                <td>${(item.Similarity_Score * 100).toFixed(2)}%</td>
                <td><button onclick="viewDetails()">View Details</button></td>
            `;
            resultsTable.appendChild(row);
        });

        // Hide loading
        loading.classList.add('hidden');
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing the resumes.');
        loading.classList.add('hidden');
    }
});

function viewDetails() {
    alert('View Details functionality is not implemented yet.');
}

function downloadResumes() {
    alert('Download functionality is not implemented yet.');
}