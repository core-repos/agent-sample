"""
Cost Tracking API endpoints for advanced cost monitoring
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from agents.bigquery.database import BigQueryConnection
import logging
import pandas as pd
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/cost-tracking", tags=["cost-tracking"])

# Request/Response models
class AnomalyDetectionRequest(BaseModel):
    days_back: int = 30
    sensitivity: float = 2.0  # Standard deviations for anomaly threshold
    group_by: Optional[str] = None  # cto, application, cloud, etc.

class AnomalyDetectionResponse(BaseModel):
    success: bool
    anomalies: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]

class ThresholdMonitoringRequest(BaseModel):
    threshold_type: str  # "budget", "daily_limit", "monthly_limit"
    threshold_value: float
    scope: Optional[str] = None  # cto, application, etc.
    scope_value: Optional[str] = None

class ThresholdMonitoringResponse(BaseModel):
    success: bool
    violations: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]

class CostForecastRequest(BaseModel):
    forecast_days: int = 30
    group_by: Optional[str] = None
    include_confidence_interval: bool = True

class CostForecastResponse(BaseModel):
    success: bool
    forecast: List[Dict[str, Any]]
    model_metrics: Dict[str, Any]
    metadata: Dict[str, Any]

class OptimizationRecommendationsResponse(BaseModel):
    success: bool
    recommendations: List[Dict[str, Any]]
    potential_savings: Dict[str, Any]
    metadata: Dict[str, Any]

# Initialize database connection
def get_db_connection():
    """Get BigQuery database connection"""
    return BigQueryConnection()

@router.post("/anomaly-detection", response_model=AnomalyDetectionResponse)
async def detect_cost_anomalies(request: AnomalyDetectionRequest):
    """Detect cost anomalies using statistical analysis"""
    try:
        db = get_db_connection()

        # Build SQL query for anomaly detection
        base_query = f"""
        WITH daily_costs AS (
            SELECT
                date,
                {request.group_by or "'total'"} as group_key,
                SUM(cost) as daily_cost
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {request.days_back} DAY)
            GROUP BY date, group_key
        ),
        cost_stats AS (
            SELECT
                group_key,
                AVG(daily_cost) as mean_cost,
                STDDEV(daily_cost) as std_cost,
                MIN(daily_cost) as min_cost,
                MAX(daily_cost) as max_cost,
                COUNT(*) as days_count
            FROM daily_costs
            GROUP BY group_key
        )
        SELECT
            dc.date,
            dc.group_key,
            dc.daily_cost,
            cs.mean_cost,
            cs.std_cost,
            ABS(dc.daily_cost - cs.mean_cost) / NULLIF(cs.std_cost, 0) as z_score
        FROM daily_costs dc
        JOIN cost_stats cs ON dc.group_key = cs.group_key
        WHERE cs.std_cost > 0
        ORDER BY dc.date DESC, dc.group_key
        """

        # Execute query
        df = pd.read_sql(base_query, db.get_connection())

        # Identify anomalies
        anomalies = []
        anomaly_threshold = request.sensitivity

        for _, row in df.iterrows():
            if row['z_score'] > anomaly_threshold:
                anomaly_type = "spike" if row['daily_cost'] > row['mean_cost'] else "drop"
                anomalies.append({
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "group": row['group_key'],
                    "actual_cost": float(row['daily_cost']),
                    "expected_cost": float(row['mean_cost']),
                    "deviation": float(row['daily_cost'] - row['mean_cost']),
                    "z_score": float(row['z_score']),
                    "anomaly_type": anomaly_type,
                    "severity": "high" if row['z_score'] > 3 else "medium"
                })

        # Generate summary
        summary = {
            "total_anomalies": len(anomalies),
            "high_severity": len([a for a in anomalies if a['severity'] == 'high']),
            "medium_severity": len([a for a in anomalies if a['severity'] == 'medium']),
            "spike_anomalies": len([a for a in anomalies if a['anomaly_type'] == 'spike']),
            "drop_anomalies": len([a for a in anomalies if a['anomaly_type'] == 'drop']),
            "analysis_period": f"{request.days_back} days",
            "sensitivity_threshold": request.sensitivity
        }

        return AnomalyDetectionResponse(
            success=True,
            anomalies=anomalies,
            summary=summary,
            metadata={
                "analysis_date": datetime.now().isoformat(),
                "records_analyzed": len(df),
                "group_by": request.group_by or "total"
            }
        )

    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threshold-monitoring", response_model=ThresholdMonitoringResponse)
async def monitor_cost_thresholds(request: ThresholdMonitoringRequest):
    """Monitor cost thresholds and budget violations"""
    try:
        db = get_db_connection()

        # Build query based on threshold type
        if request.threshold_type == "budget":
            # Compare actual vs budget
            query = f"""
            WITH current_spending AS (
                SELECT
                    cto,
                    tr_product_pillar_team,
                    tr_product_id,
                    tr_product,
                    SUM(cost) as ytd_actual_spend
                FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
                WHERE date >= '2025-02-01'  -- FY26 start
                GROUP BY cto, tr_product_pillar_team, tr_product_id, tr_product
            )
            SELECT
                cs.cto,
                cs.tr_product_pillar_team,
                cs.tr_product_id,
                cs.tr_product,
                cs.ytd_actual_spend,
                b.fy_26_budget,
                b.fy26_ytd_spend as budget_ytd_spend,
                (cs.ytd_actual_spend / NULLIF(b.fy_26_budget, 0)) * 100 as budget_utilization_pct,
                CASE
                    WHEN cs.ytd_actual_spend > b.fy_26_budget THEN 'over_budget'
                    WHEN (cs.ytd_actual_spend / NULLIF(b.fy_26_budget, 0)) > 0.9 THEN 'approaching_limit'
                    ELSE 'within_budget'
                END as status
            FROM current_spending cs
            LEFT JOIN `{db.project_id}`.`{db.dataset_id}`.`budget_analysis` b
                ON cs.tr_product_id = b.tr_product_id
            WHERE b.fy_26_budget IS NOT NULL
            """

        elif request.threshold_type == "daily_limit":
            # Check daily spending limits
            query = f"""
            SELECT
                date,
                {request.scope or "'total'"} as scope_key,
                SUM(cost) as daily_cost,
                {request.threshold_value} as threshold_value,
                CASE
                    WHEN SUM(cost) > {request.threshold_value} THEN 'exceeded'
                    WHEN SUM(cost) > {request.threshold_value * 0.9} THEN 'approaching'
                    ELSE 'within_limit'
                END as status
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            GROUP BY date, scope_key
            HAVING SUM(cost) > {request.threshold_value * 0.8}  -- Show when >80% of threshold
            ORDER BY date DESC
            """

        else:  # monthly_limit
            query = f"""
            WITH monthly_costs AS (
                SELECT
                    DATE_TRUNC(date, MONTH) as month,
                    {request.scope or "'total'"} as scope_key,
                    SUM(cost) as monthly_cost
                FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
                WHERE date >= DATE_SUB(DATE_TRUNC(CURRENT_DATE(), MONTH), INTERVAL 3 MONTH)
                GROUP BY month, scope_key
            )
            SELECT
                month,
                scope_key,
                monthly_cost,
                {request.threshold_value} as threshold_value,
                CASE
                    WHEN monthly_cost > {request.threshold_value} THEN 'exceeded'
                    WHEN monthly_cost > {request.threshold_value * 0.9} THEN 'approaching'
                    ELSE 'within_limit'
                END as status
            FROM monthly_costs
            WHERE monthly_cost > {request.threshold_value * 0.8}
            ORDER BY month DESC, scope_key
            """

        # Execute query
        df = pd.read_sql(query, db.get_connection())

        # Process violations
        violations = []
        for _, row in df.iterrows():
            if row['status'] in ['exceeded', 'over_budget', 'approaching_limit', 'approaching']:
                violation = {
                    "scope": row.get('scope_key', row.get('tr_product', 'total')),
                    "status": row['status'],
                    "threshold_value": float(request.threshold_value) if request.threshold_type != "budget" else float(row.get('fy_26_budget', 0)),
                    "severity": "high" if row['status'] in ['exceeded', 'over_budget'] else "medium"
                }

                if request.threshold_type == "budget":
                    violation.update({
                        "actual_spend": float(row['ytd_actual_spend']),
                        "budget": float(row['fy_26_budget']),
                        "utilization_pct": float(row['budget_utilization_pct']),
                        "overage": float(row['ytd_actual_spend'] - row['fy_26_budget']) if row['status'] == 'over_budget' else 0
                    })
                else:
                    violation.update({
                        "actual_cost": float(row.get('daily_cost', row.get('monthly_cost', 0))),
                        "date": row.get('date', row.get('month', '')).strftime('%Y-%m-%d') if hasattr(row.get('date', row.get('month', '')), 'strftime') else str(row.get('date', row.get('month', ''))),
                        "overage": float(row.get('daily_cost', row.get('monthly_cost', 0)) - request.threshold_value) if row['status'] == 'exceeded' else 0
                    })

                violations.append(violation)

        # Generate summary
        summary = {
            "total_violations": len(violations),
            "high_severity": len([v for v in violations if v['severity'] == 'high']),
            "medium_severity": len([v for v in violations if v['severity'] == 'medium']),
            "threshold_type": request.threshold_type,
            "threshold_value": request.threshold_value
        }

        return ThresholdMonitoringResponse(
            success=True,
            violations=violations,
            summary=summary,
            metadata={
                "analysis_date": datetime.now().isoformat(),
                "scope": request.scope,
                "scope_value": request.scope_value
            }
        )

    except Exception as e:
        logger.error(f"Threshold monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast", response_model=CostForecastResponse)
async def forecast_costs(request: CostForecastRequest):
    """Generate cost forecasts using trend analysis"""
    try:
        db = get_db_connection()

        # Get historical data for forecasting
        query = f"""
        SELECT
            date,
            {request.group_by or "'total'"} as group_key,
            SUM(cost) as daily_cost
        FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
        GROUP BY date, group_key
        ORDER BY date ASC
        """

        df = pd.read_sql(query, db.get_connection())

        forecasts = []
        model_metrics = {}

        # Generate forecast for each group
        for group in df['group_key'].unique():
            group_data = df[df['group_key'] == group].copy()
            # Convert date column to datetime if it's not already
            group_data['date'] = pd.to_datetime(group_data['date'])
            group_data['days_from_start'] = (group_data['date'] - group_data['date'].min()).dt.days

            # Simple linear regression for trend
            x = group_data['days_from_start'].values
            y = group_data['daily_cost'].values

            if len(x) > 10:  # Need sufficient data
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                # Generate future predictions
                last_day = x.max()
                future_days = range(last_day + 1, last_day + request.forecast_days + 1)

                for day in future_days:
                    predicted_cost = intercept + slope * day
                    forecast_date = group_data['date'].min() + timedelta(days=day)

                    forecast_item = {
                        "date": forecast_date.strftime('%Y-%m-%d'),
                        "group": group,
                        "predicted_cost": float(max(0, predicted_cost)),  # Ensure non-negative
                        "trend": "increasing" if slope > 0 else "decreasing",
                        "confidence": float(r_value ** 2)  # R-squared as confidence measure
                    }

                    if request.include_confidence_interval:
                        # Simple confidence interval based on standard error
                        margin_error = 1.96 * std_err * np.sqrt(1 + 1/len(x) + (day - np.mean(x))**2 / np.sum((x - np.mean(x))**2))
                        forecast_item.update({
                            "lower_bound": float(max(0, predicted_cost - margin_error)),
                            "upper_bound": float(predicted_cost + margin_error)
                        })

                    forecasts.append(forecast_item)

                # Store model metrics
                model_metrics[group] = {
                    "r_squared": float(r_value ** 2),
                    "slope": float(slope),
                    "p_value": float(p_value),
                    "data_points": len(x)
                }

        return CostForecastResponse(
            success=True,
            forecast=forecasts,
            model_metrics=model_metrics,
            metadata={
                "analysis_date": datetime.now().isoformat(),
                "forecast_days": request.forecast_days,
                "group_by": request.group_by or "total",
                "historical_days": 90
            }
        )

    except Exception as e:
        logger.error(f"Cost forecasting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimization-recommendations", response_model=OptimizationRecommendationsResponse)
async def get_optimization_recommendations():
    """Generate cost optimization recommendations"""
    try:
        db = get_db_connection()

        recommendations = []
        potential_savings = {"total": 0, "by_category": {}}

        # 1. Identify unused or underutilized resources
        unused_query = f"""
        WITH recent_usage AS (
            SELECT
                application,
                service_name,
                managed_service,
                environment,
                AVG(cost) as avg_daily_cost,
                COUNT(*) as days_active,
                MAX(date) as last_active_date
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY application, service_name, managed_service, environment
        )
        SELECT *
        FROM recent_usage
        WHERE avg_daily_cost < 1.0 OR days_active < 15  -- Low usage threshold
        ORDER BY avg_daily_cost DESC
        """

        unused_df = pd.read_sql(unused_query, db.get_connection())

        for _, row in unused_df.head(10).iterrows():
            potential_saving = row['avg_daily_cost'] * 30 * 0.8  # 80% savings potential
            recommendations.append({
                "type": "unused_resource",
                "priority": "medium",
                "resource": f"{row['application']} - {row['service_name']}",
                "description": f"Resource has low usage (${row['avg_daily_cost']:.2f}/day) in {row['environment']} environment",
                "potential_monthly_savings": float(potential_saving),
                "action": "Consider decommissioning or right-sizing"
            })
            potential_savings["total"] += potential_saving

        # 2. Identify cost spikes compared to historical averages
        spike_query = f"""
        WITH cost_comparison AS (
            SELECT
                cloud,
                managed_service,
                AVG(CASE WHEN date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) THEN cost END) as recent_avg,
                AVG(CASE WHEN date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 37 DAY) AND DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY) THEN cost END) as historical_avg
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 37 DAY)
            GROUP BY cloud, managed_service
        )
        SELECT *,
            (recent_avg - historical_avg) as cost_increase,
            ((recent_avg - historical_avg) / NULLIF(historical_avg, 0)) * 100 as pct_increase
        FROM cost_comparison
        WHERE recent_avg > historical_avg * 1.2  -- 20% increase
        ORDER BY cost_increase DESC
        """

        spike_df = pd.read_sql(spike_query, db.get_connection())

        for _, row in spike_df.head(5).iterrows():
            potential_saving = row['cost_increase'] * 30 * 0.5  # 50% of increase could be optimized
            recommendations.append({
                "type": "cost_spike",
                "priority": "high",
                "resource": f"{row['cloud']} - {row['managed_service']}",
                "description": f"Cost increased by {row['pct_increase']:.1f}% recently (${row['cost_increase']:.2f}/day increase)",
                "potential_monthly_savings": float(potential_saving),
                "action": "Investigate recent changes and optimize configuration"
            })
            potential_savings["total"] += potential_saving

        # 3. Environment distribution analysis
        env_query = f"""
        SELECT
            environment,
            COUNT(DISTINCT application) as app_count,
            SUM(cost) as total_cost,
            AVG(cost) as avg_cost
        FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY environment
        """

        env_df = pd.read_sql(env_query, db.get_connection())

        non_prod_cost = env_df[env_df['environment'] == 'NON-PROD']['total_cost'].sum() if len(env_df[env_df['environment'] == 'NON-PROD']) > 0 else 0
        if non_prod_cost > 0:
            potential_saving = non_prod_cost * 0.3  # 30% savings potential in non-prod
            recommendations.append({
                "type": "environment_optimization",
                "priority": "medium",
                "resource": "Non-Production Environment",
                "description": f"Non-production costs are ${non_prod_cost:.2f}/month",
                "potential_monthly_savings": float(potential_saving),
                "action": "Implement auto-scaling, scheduled shutdown, or right-sizing for non-prod resources"
            })
            potential_savings["total"] += potential_saving

        # Calculate savings by category
        potential_savings["by_category"] = {
            "unused_resources": sum([r["potential_monthly_savings"] for r in recommendations if r["type"] == "unused_resource"]),
            "cost_optimization": sum([r["potential_monthly_savings"] for r in recommendations if r["type"] == "cost_spike"]),
            "environment_optimization": sum([r["potential_monthly_savings"] for r in recommendations if r["type"] == "environment_optimization"])
        }

        return OptimizationRecommendationsResponse(
            success=True,
            recommendations=recommendations,
            potential_savings=potential_savings,
            metadata={
                "analysis_date": datetime.now().isoformat(),
                "analysis_period": "30 days",
                "recommendation_count": len(recommendations)
            }
        )

    except Exception as e:
        logger.error(f"Optimization recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard-summary")
async def get_cost_dashboard_summary():
    """Get summary data for cost tracking dashboard"""
    try:
        db = get_db_connection()

        # Get current period summary
        summary_query = f"""
        WITH current_period AS (
            SELECT
                SUM(cost) as total_cost,
                COUNT(DISTINCT application) as unique_applications,
                COUNT(DISTINCT cto) as unique_organizations,
                AVG(cost) as avg_daily_cost
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        ),
        previous_period AS (
            SELECT
                SUM(cost) as prev_total_cost,
                AVG(cost) as prev_avg_daily_cost
            FROM `{db.project_id}`.`{db.dataset_id}`.`cost_analysis`
            WHERE date BETWEEN DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
                          AND DATE_SUB(CURRENT_DATE(), INTERVAL 31 DAY)
        )
        SELECT
            cp.*,
            pp.prev_total_cost,
            pp.prev_avg_daily_cost,
            ((cp.total_cost - pp.prev_total_cost) / NULLIF(pp.prev_total_cost, 0)) * 100 as cost_change_pct
        FROM current_period cp
        CROSS JOIN previous_period pp
        """

        summary_df = pd.read_sql(summary_query, db.get_connection())
        summary_row = summary_df.iloc[0]

        return {
            "success": True,
            "summary": {
                "current_month_cost": float(summary_row['total_cost']),
                "previous_month_cost": float(summary_row['prev_total_cost']),
                "cost_change_percentage": float(summary_row['cost_change_pct']),
                "unique_applications": int(summary_row['unique_applications']),
                "unique_organizations": int(summary_row['unique_organizations']),
                "avg_daily_cost": float(summary_row['avg_daily_cost']),
                "analysis_period": "Last 30 days"
            },
            "metadata": {
                "generated_at": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Dashboard summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))