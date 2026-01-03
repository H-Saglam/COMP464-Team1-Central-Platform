-- ============================================
-- Hospital Supply Chain Database Schema
-- PostgreSQL Initialization Script
-- ============================================

-- Create custom ENUM types
CREATE TYPE event_source_type AS ENUM ('SOA', 'Serverless');
CREATE TYPE order_status_type AS ENUM ('PENDING', 'APPROVED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED');
CREATE TYPE priority_type AS ENUM ('URGENT', 'HIGH', 'NORMAL');
CREATE TYPE decision_type AS ENUM ('ORDER_CREATED', 'ORDER_SKIPPED', 'THRESHOLD_ADJUSTED', 'ALERT_SENT');
CREATE TYPE architecture_type AS ENUM ('SOA', 'Serverless');
CREATE TYPE log_status_type AS ENUM ('SUCCESS', 'FAILED', 'TIMEOUT', 'PARTIAL');

-- ============================================
-- Table: StockEvents
-- Stores all incoming stock/inventory events
-- ============================================
CREATE TABLE StockEvents (
    event_id VARCHAR(100) PRIMARY KEY,
    hospital_id VARCHAR(50) NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    current_stock_units INTEGER NOT NULL CHECK (current_stock_units >= 0),
    daily_consumption_units INTEGER NOT NULL CHECK (daily_consumption_units >= 0),
    days_of_supply DECIMAL(10, 2) NOT NULL CHECK (days_of_supply >= 0),
    event_source event_source_type NOT NULL,
    received_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_timestamp TIMESTAMP WITH TIME ZONE,

    -- Additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for StockEvents
CREATE INDEX idx_stock_events_hospital ON StockEvents(hospital_id);
CREATE INDEX idx_stock_events_product ON StockEvents(product_code);
CREATE INDEX idx_stock_events_hospital_product ON StockEvents(hospital_id, product_code);
CREATE INDEX idx_stock_events_received_timestamp ON StockEvents(received_timestamp DESC);
CREATE INDEX idx_stock_events_source ON StockEvents(event_source);

-- ============================================
-- Table: Orders
-- Stores all supply orders (automatic and manual)
-- ============================================
CREATE TABLE Orders (
    order_id VARCHAR(100) PRIMARY KEY,
    hospital_id VARCHAR(50) NOT NULL,
    product_code VARCHAR(50) NOT NULL,
    order_quantity INTEGER NOT NULL CHECK (order_quantity > 0),
    priority priority_type NOT NULL DEFAULT 'NORMAL',
    order_status order_status_type NOT NULL DEFAULT 'PENDING',
    created_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivery_timestamp TIMESTAMP WITH TIME ZONE,
    order_source event_source_type NOT NULL,

    -- Additional fields
    warehouse_id VARCHAR(50) DEFAULT 'CENTRAL-WAREHOUSE',
    estimated_delivery_date TIMESTAMP WITH TIME ZONE,
    actual_delivery_date TIMESTAMP WITH TIME ZONE,
    notes TEXT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Orders
CREATE INDEX idx_orders_hospital ON Orders(hospital_id);
CREATE INDEX idx_orders_product ON Orders(product_code);
CREATE INDEX idx_orders_status ON Orders(order_status);
CREATE INDEX idx_orders_priority ON Orders(priority);
CREATE INDEX idx_orders_created_timestamp ON Orders(created_timestamp DESC);
CREATE INDEX idx_orders_hospital_status ON Orders(hospital_id, order_status);

-- ============================================
-- Table: DecisionLogs
-- Logs all automated decisions made by the system
-- ============================================
CREATE TABLE DecisionLogs (
    decision_id VARCHAR(100) PRIMARY KEY,
    event_id VARCHAR(100) REFERENCES StockEvents(event_id) ON DELETE SET NULL,
    order_id VARCHAR(100) REFERENCES Orders(order_id) ON DELETE SET NULL,
    decision_type decision_type NOT NULL,
    decision_reason TEXT NOT NULL,
    days_of_supply_at_decision DECIMAL(10, 2) NOT NULL,
    threshold_used DECIMAL(10, 2) NOT NULL,

    -- Additional context
    algorithm_version VARCHAR(20),
    confidence_score DECIMAL(5, 4),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for DecisionLogs
CREATE INDEX idx_decision_logs_event ON DecisionLogs(event_id);
CREATE INDEX idx_decision_logs_order ON DecisionLogs(order_id);
CREATE INDEX idx_decision_logs_type ON DecisionLogs(decision_type);
CREATE INDEX idx_decision_logs_created ON DecisionLogs(created_at DESC);

-- ============================================
-- Table: ESBLogs
-- Logs all ESB (Enterprise Service Bus) messages
-- ============================================
CREATE TABLE ESBLogs (
    log_id VARCHAR(100) PRIMARY KEY,
    message_id VARCHAR(100) NOT NULL,
    source_hospital_id VARCHAR(50) NOT NULL,
    target_service VARCHAR(100) NOT NULL,
    latency_ms INTEGER NOT NULL CHECK (latency_ms >= 0),
    status log_status_type NOT NULL,

    -- Request/Response details
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for ESBLogs
CREATE INDEX idx_esb_logs_message ON ESBLogs(message_id);
CREATE INDEX idx_esb_logs_hospital ON ESBLogs(source_hospital_id);
CREATE INDEX idx_esb_logs_target ON ESBLogs(target_service);
CREATE INDEX idx_esb_logs_status ON ESBLogs(status);
CREATE INDEX idx_esb_logs_timestamp ON ESBLogs(timestamp DESC);
CREATE INDEX idx_esb_logs_latency ON ESBLogs(latency_ms);

-- ============================================
-- Table: PerformanceMetrics
-- Stores performance metrics for SOA vs Serverless comparison
-- ============================================
CREATE TABLE PerformanceMetrics (
    metric_id VARCHAR(100) PRIMARY KEY,
    architecture architecture_type NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    metric_value DECIMAL(15, 4) NOT NULL,

    -- Additional dimensions
    hospital_id VARCHAR(50),
    product_code VARCHAR(50),
    operation_name VARCHAR(100),

    -- Timestamp
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for PerformanceMetrics
CREATE INDEX idx_perf_metrics_architecture ON PerformanceMetrics(architecture);
CREATE INDEX idx_perf_metrics_type ON PerformanceMetrics(metric_type);
CREATE INDEX idx_perf_metrics_timestamp ON PerformanceMetrics(timestamp DESC);
CREATE INDEX idx_perf_metrics_arch_type ON PerformanceMetrics(architecture, metric_type);

-- ============================================
-- Trigger Functions for updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_stock_events_updated_at
    BEFORE UPDATE ON StockEvents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON Orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Sample Views for Reporting
-- ============================================

-- View: Active Low Stock Alerts
CREATE VIEW vw_active_low_stock AS
SELECT
    se.event_id,
    se.hospital_id,
    se.product_code,
    se.current_stock_units,
    se.days_of_supply,
    se.event_source,
    se.received_timestamp
FROM StockEvents se
WHERE se.days_of_supply < 7
  AND se.processed_timestamp IS NULL
ORDER BY se.days_of_supply ASC;

-- View: Order Summary by Hospital
CREATE VIEW vw_order_summary_by_hospital AS
SELECT
    o.hospital_id,
    o.order_status,
    COUNT(*) as order_count,
    SUM(o.order_quantity) as total_quantity,
    AVG(o.order_quantity) as avg_quantity
FROM Orders o
GROUP BY o.hospital_id, o.order_status;

-- View: Architecture Performance Comparison
CREATE VIEW vw_architecture_performance AS
SELECT
    pm.architecture,
    pm.metric_type,
    COUNT(*) as sample_count,
    AVG(pm.metric_value) as avg_value,
    MIN(pm.metric_value) as min_value,
    MAX(pm.metric_value) as max_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pm.metric_value) as median_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY pm.metric_value) as p95_value
FROM PerformanceMetrics pm
GROUP BY pm.architecture, pm.metric_type;

-- ============================================
-- Grant Permissions (adjust as needed)
-- ============================================
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;

-- ============================================
-- Comments for Documentation
-- ============================================
COMMENT ON TABLE StockEvents IS 'Stores all incoming inventory/stock events from hospitals';
COMMENT ON TABLE Orders IS 'Stores all supply orders, both automatic and manual';
COMMENT ON TABLE DecisionLogs IS 'Audit log of all automated ordering decisions';
COMMENT ON TABLE ESBLogs IS 'Enterprise Service Bus message logs for SOA architecture';
COMMENT ON TABLE PerformanceMetrics IS 'Performance metrics for SOA vs Serverless comparison';

COMMENT ON COLUMN StockEvents.event_source IS 'Whether event came from SOA or Serverless architecture';
COMMENT ON COLUMN Orders.order_source IS 'Which architecture triggered this order';
COMMENT ON COLUMN DecisionLogs.threshold_used IS 'The days-of-supply threshold that was used for the decision';
COMMENT ON COLUMN ESBLogs.latency_ms IS 'End-to-end latency in milliseconds';
COMMENT ON COLUMN PerformanceMetrics.metric_type IS 'Type of metric: latency, throughput, error_rate, etc.';
