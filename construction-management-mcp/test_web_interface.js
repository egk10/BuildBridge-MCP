// Test the web interface API functionality
const API_BASE = 'http://localhost:8000';

async function testDashboardData() {
    try {
        console.log('Testing dashboard data loading...');
        
        const payload = {
            query: 'Show me all projects',
            type: 'search_projects'
        };

        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response:', {
            success: data.success,
            projectCount: data.data.count,
            firstProject: data.data.results[0] ? {
                name: data.data.results[0].Project_Name,
                status: data.data.results[0].Status,
                budget: data.data.results[0].Total_Budget,
                progress: data.data.results[0].Progress_Percent
            } : null
        });

        // Test dashboard calculations
        const projects = data.data.results;
        const totalBudget = projects.reduce((sum, p) => sum + (p.Total_Budget || 0), 0);
        const activeProjects = projects.filter(p => p.Status !== 'Completed').length;
        const avgProgress = projects.reduce((sum, p) => sum + (p.Progress_Percent || 0), 0) / projects.length;

        console.log('Dashboard Stats:', {
            totalProjects: projects.length,
            totalBudget: totalBudget.toLocaleString(),
            activeProjects,
            avgProgress: avgProgress.toFixed(1) + '%'
        });

        console.log('✅ Dashboard data loading test passed!');
        return true;
    } catch (error) {
        console.error('❌ Dashboard test failed:', error);
        return false;
    }
}

// Run the test
testDashboardData();