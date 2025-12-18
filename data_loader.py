import pandas as pd

def standardize_columns(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df

def auto_rename_id(df, possible_names, standard_name):
    for name in possible_names:
        if name in df.columns:
            df.rename(columns={name: standard_name}, inplace=True)
            return df
    return df

def load_all_data():
    orders = standardize_columns(pd.read_csv("data/orders.csv"))
    delivery = standardize_columns(pd.read_csv("data/delivery_performance.csv"))
    routes = standardize_columns(pd.read_csv("data/routes_distance.csv"))
    vehicles = standardize_columns(pd.read_csv("data/vehicle_fleet.csv"))
    costs = standardize_columns(pd.read_csv("data/cost_breakdown.csv"))
    warehouse = standardize_columns(pd.read_csv("data/warehouse_inventory.csv"))
    feedback = standardize_columns(pd.read_csv("data/customer_feedback.csv"))

    # -------- AUTO RENAME IDS --------
    orders = auto_rename_id(orders, ["orderid", "order_id"], "order_id")
    delivery = auto_rename_id(delivery, ["orderid", "order_id"], "order_id")
    costs = auto_rename_id(costs, ["orderid", "order_id"], "order_id")
    routes = auto_rename_id(routes, ["orderid", "order_id"], "order_id")
    feedback = auto_rename_id(feedback, ["orderid", "order_id"], "order_id")

    vehicles = auto_rename_id(vehicles, ["vehicleid", "vehicle_id"], "vehicle_id")
    warehouse = auto_rename_id(warehouse, ["warehouseid", "warehouse_id"], "warehouse_id")

    # Extract route as route_id for proper join key
    if "route" in routes.columns:
        routes["route_id"] = routes["route"]
    
    # Create customer_id from customer_segment for proper data modeling
    if "customer_segment" in orders.columns and "customer_id" not in orders.columns:
        orders["customer_id"] = orders["customer_segment"] + "_" + orders["order_id"].astype(str).str[-4:]

    # -------- MERGES --------
    df = orders.merge(delivery, on="order_id", how="left")
    
    # ✅ FIX 1: Join routes on both order_id AND route (to get route distance data)
    df = df.merge(routes, on="order_id", how="left")
    
    df = df.merge(costs, on="order_id", how="left")
    
    # ✅ FIX 2: Join feedback on customer_id (customer-level data)
    # First, add customer_id to feedback based on order mapping
    if "customer_id" in df.columns:
        order_to_customer = df[["order_id", "customer_id"]].drop_duplicates()
        feedback = feedback.merge(order_to_customer, on="order_id", how="left")
        df = df.merge(
            feedback.drop(columns=["order_id"]).drop_duplicates(subset=["customer_id"]),
            on="customer_id",
            how="left"
        )
    else:
        df = df.merge(feedback, on="order_id", how="left")
    
    # ✅ IMPROVEMENT 1: Avoid silent overwrites - check before setting defaults
    if "route_distance_km" not in df.columns:
        if "distance_km" in df.columns:
            df["route_distance_km"] = df["distance_km"]
        else:
            df["route_distance_km"] = 100
    
    if "vehicle_capacity" not in df.columns:
        df["vehicle_capacity"] = 1000
    
    if "warehouse_load" not in df.columns:
        df["warehouse_load"] = 50
    
    if "delivery_priority" not in df.columns:
        if "priority" in df.columns:
            df["delivery_priority"] = df["priority"]
        else:
            df["delivery_priority"] = "medium"
    
    if "fuel_cost" not in df.columns:
        df["fuel_cost"] = 500
    
    if "maintenance_cost" not in df.columns:
        if "vehicle_maintenance" in df.columns:
            df["maintenance_cost"] = df["vehicle_maintenance"]
        else:
            df["maintenance_cost"] = 200
    
    if "actual_delivery_days" not in df.columns:
        df["actual_delivery_days"] = 5
    
    if "expected_delivery_days" not in df.columns:
        if "promised_delivery_days" in df.columns:
            df["expected_delivery_days"] = df["promised_delivery_days"]
        else:
            df["expected_delivery_days"] = 3
    
    if "total_cost" not in df.columns:
        cost_columns = [c for c in df.columns if 'cost' in c.lower() or 'charge' in c.lower()]
        if cost_columns:
            df["total_cost"] = df[cost_columns].sum(axis=1, skipna=True)
        else:
            df["total_cost"] = 1000
    
    if "feedback_score" not in df.columns:
        if "rating" in df.columns:
            df["feedback_score"] = df["rating"]
        else:
            df["feedback_score"] = 3
    
    if "fuel_consumption_rate" not in df.columns:
        if "fuel_consumption_l" in df.columns:
            df["fuel_consumption_rate"] = df["fuel_consumption_l"]
        else:
            df["fuel_consumption_rate"] = 5

    return df
