-- Construction MCP Database Initialization
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (though it should be created by POSTGRES_DB env var)
-- SELECT 'CREATE DATABASE construction_mcp' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'construction_mcp')\gexec

-- Connect to the construction_mcp database
\c construction_mcp;

-- Create tables for Construction MCP
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    budget DECIMAL(15,2),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_phases (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    phase_name VARCHAR(100) NOT NULL,
    phase_order INTEGER,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'planned',
    budget DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS safety_incidents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    incident_date DATE NOT NULL,
    incident_type VARCHAR(100),
    severity VARCHAR(50),
    description TEXT,
    corrective_action TEXT,
    reported_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budget_tracking (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    budgeted_amount DECIMAL(15,2),
    actual_amount DECIMAL(15,2),
    variance DECIMAL(15,2),
    period DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resources (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    resource_type VARCHAR(50),
    resource_name VARCHAR(100),
    quantity INTEGER,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(15,2),
    status VARCHAR(50) DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quality_checks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    check_date DATE NOT NULL,
    check_type VARCHAR(100),
    component VARCHAR(100),
    result VARCHAR(50),
    inspector VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_dates ON projects(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_safety_incidents_date ON safety_incidents(incident_date);
CREATE INDEX IF NOT EXISTS idx_budget_tracking_project ON budget_tracking(project_id);
CREATE INDEX IF NOT EXISTS idx_resources_project ON resources(project_id);
CREATE INDEX IF NOT EXISTS idx_quality_checks_project ON quality_checks(project_id);

-- Insert some sample data for testing
INSERT INTO projects (project_id, name, description, budget, start_date, end_date) VALUES
('PROJ-001', 'Downtown Office Complex', 'Modern office building construction', 2500000.00, '2024-01-15', '2025-06-30'),
('PROJ-002', 'Residential Tower', 'High-rise residential building', 5000000.00, '2024-03-01', '2026-02-28'),
('PROJ-003', 'Shopping Mall Renovation', 'Complete renovation of existing mall', 1800000.00, '2024-02-01', '2024-11-30')
ON CONFLICT (project_id) DO NOTHING;

-- Insert sample budget tracking data
INSERT INTO budget_tracking (project_id, category, budgeted_amount, actual_amount, period) VALUES
(1, 'Labor', 800000.00, 750000.00, '2024-09-01'),
(1, 'Materials', 1200000.00, 1150000.00, '2024-09-01'),
(1, 'Equipment', 500000.00, 480000.00, '2024-09-01'),
(2, 'Labor', 1500000.00, 1450000.00, '2024-09-01'),
(2, 'Materials', 2500000.00, 2400000.00, '2024-09-01'),
(3, 'Labor', 600000.00, 580000.00, '2024-09-01'),
(3, 'Materials', 900000.00, 850000.00, '2024-09-01')
ON CONFLICT DO NOTHING;

-- Insert sample safety incidents
INSERT INTO safety_incidents (project_id, incident_date, incident_type, severity, description, corrective_action) VALUES
(1, '2024-08-15', 'Slip and Fall', 'Minor', 'Worker slipped on wet floor in construction area', 'Improved floor signage and drainage'),
(2, '2024-07-22', 'Equipment Malfunction', 'Moderate', 'Crane malfunction during lifting operation', 'Scheduled maintenance and operator retraining'),
(1, '2024-09-05', 'Near Miss', 'Low', 'Worker nearly struck by falling debris', 'Enhanced PPE requirements and safety briefings')
ON CONFLICT DO NOTHING;

-- Insert sample resources
INSERT INTO resources (project_id, resource_type, resource_name, quantity, unit_cost, total_cost) VALUES
(1, 'Equipment', 'Excavator', 2, 50000.00, 100000.00),
(1, 'Labor', 'Construction Workers', 25, 35000.00, 875000.00),
(2, 'Equipment', 'Concrete Mixer', 3, 25000.00, 75000.00),
(2, 'Labor', 'Skilled Labor', 40, 40000.00, 1600000.00),
(3, 'Equipment', 'Painting Equipment', 5, 5000.00, 25000.00),
(3, 'Labor', 'Renovation Crew', 15, 30000.00, 450000.00)
ON CONFLICT DO NOTHING;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcpuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcpuser;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();